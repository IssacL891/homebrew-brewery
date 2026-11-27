"""Publish scoped bump branches and request native GitHub auto-merge."""

import argparse
from base64 import b64encode
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import quote, urlencode

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.bumps import PackageResult, result_from_json
from automation.manifests import ManifestError, load_manifest, yaml_parser
from automation.package_diff import prepare_bump
from automation.pr_validation import FULL_SHA, bump_branch, git
from automation.releases import ReleaseError, version_key


class PublishError(ValueError):
    """A repository or package publishing step failed."""


@dataclass(frozen=True)
class PublishResult:
    kind: str
    token: str
    status: str
    message: str
    stage: str = "publish"


def pending_version(pull: dict, package: PackageResult) -> str | None:
    title = pull.get("title", "")
    prefix = f"{package.token} "
    if not title.startswith(prefix):
        return None
    head = pull.get("head", {}).get("ref", "")
    kind_branch = f"brewery-bump/{package.kind}/{package.token}/"
    if head.startswith(kind_branch) or (package.kind == "cask" and head.startswith(f"bump-{package.token}-")):
        return title.removeprefix(prefix)
    return None


def publish_one(api, base: str, package: PackageResult, current: str, open_prs: list[dict]) -> PublishResult:
    candidate = package.candidate
    if candidate is None or not package.files:
        raise PublishError("release candidate has no verified package diff")
    title = f"{package.token} {candidate.version}"
    branch = bump_branch(package.kind, package.token, candidate.version)
    existing = api.find_prs(branch)
    open_match = next((pr for pr in existing if pr["state"] == "open"), None)

    if open_match:
        if (
            open_match["user"]["login"] != api.app_login or
            (open_match["head"].get("repo") or {}).get("full_name") != api.repository or
            open_match["base"]["ref"] != api.default_branch
        ):
            return PublishResult(package.kind, package.token, "skipped", "branch already has a non-app PR")
        number = open_match["number"]
        sha = api.verify_and_refresh(package, base, branch, open_match["head"]["sha"], number)
        api.queue_merge(number, sha)
        return PublishResult(package.kind, package.token, "pending", f"PR #{number} awaiting validation")

    if existing:
        return PublishResult(package.kind, package.token, "skipped", "candidate already has a closed PR")

    for pr in open_prs:
        version = pending_version(pr, package)
        if version is None:
            continue
        try:
            stale = version_key(version) <= version_key(current)
        except ReleaseError:
            stale = False
        if stale:
            print(f"{package.kind}:{package.token} stale PR #{pr['number']} already matched or superseded")
        else:
            return PublishResult(package.kind, package.token, "skipped", f"pending candidate in PR #{pr['number']}")

    current_head = api.get_branch_sha(branch)
    if current_head:
        if not api.owns_initial_commit(current_head):
            raise PublishError("existing branch ownership could not be verified")
        head = api.verify_and_refresh(package, base, branch, current_head, None)
    else:
        head = api.create_commit(branch, base, title, package.files)
    pr = api.create_pr(branch, title)
    api.queue_merge(pr["number"], head)
    return PublishResult(package.kind, package.token, "published", pr["html_url"])


def publish_bumps(api, base: str, packages: list[PackageResult], current_versions: dict) -> list[PublishResult]:
    open_prs = api.list_open()
    results = []
    for package in packages:
        if package.status != "candidate":
            results.append(PublishResult(package.kind, package.token, package.status, package.message, "scan"))
            continue
        try:
            results.append(publish_one(api, base, package, current_versions[package.kind, package.token], open_prs))
        except (PublishError, ManifestError, ReleaseError, OSError, subprocess.SubprocessError) as exc:
            message = str(exc) if isinstance(exc, PublishError) else "could not verify or publish the candidate"
            results.append(PublishResult(package.kind, package.token, "warning", message))
    return results


CREATE_COMMIT = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid } }
}
"""


class GitHub:
    default_branch = "main"

    def __init__(self, root: Path, repository: str, app_login: str):
        self.root = root
        self.repository = repository
        self.app_login = app_login
        self.owner = repository.split("/", 1)[0]
        self.path = f"repos/{repository}"

    def command(self, args: list[str], *, label: str, data=None, parse=True):
        try:
            result = subprocess.run(
                ["gh", *args], input=json.dumps(data) if data is not None else None,
                capture_output=True, text=True, check=True, timeout=60,
            ).stdout
            return json.loads(result) if parse else result
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            raise PublishError(label) from None

    def api(self, endpoint: str, *, label: str, data=None, method="GET", paginate=False):
        args = ["api"]
        if paginate:
            args.extend(["--paginate", "--slurp"])
        if data is not None:
            args.extend(["--method", method, "--input", "-"])
        return self.command([*args, endpoint], label=label, data=data)

    def list_open(self) -> list[dict]:
        return self.list_prs(state="open", base=self.default_branch)

    def find_prs(self, branch: str) -> list[dict]:
        return self.list_prs(state="all", base=self.default_branch, head=f"{self.owner}:{branch}")

    def list_prs(self, **filters) -> list[dict]:
        query = urlencode({**filters, "per_page": 100})
        pages = self.api(f"{self.path}/pulls?{query}", label="could not read existing PRs", paginate=True)
        return [pr for page in pages for pr in page]

    def get_branch_sha(self, branch: str) -> str | None:
        refs = self.api(f"{self.path}/git/matching-refs/heads/{quote(branch, safe='/')}", label="could not read branch")
        return next((ref["object"]["sha"] for ref in refs if ref["ref"] == f"refs/heads/{branch}"), None)

    def owns_initial_commit(self, sha: str) -> bool:
        commit = self.api(f"{self.path}/commits/{sha}", label="could not verify existing branch owner")
        return (
            (commit.get("author") or {}).get("login") == self.app_login and
            commit["commit"]["verification"]["verified"] is True
        )

    def create_commit(self, branch: str, base: str, title: str, files: dict[Path, str]) -> str:
        self.api(f"{self.path}/git/refs", method="POST", label="could not create the bump branch",
                 data={"ref": f"refs/heads/{branch}", "sha": base})
        response = self.api("graphql", method="POST", label="could not create the signed bump commit", data={
            "query": CREATE_COMMIT,
            "variables": {"input": {
                "branch": {"repositoryNameWithOwner": self.repository, "branchName": branch},
                "expectedHeadOid": base,
                "message": {"headline": title},
                "fileChanges": {"additions": [{
                    "path": path.as_posix(), "contents": b64encode(contents.encode()).decode(),
                } for path, contents in files.items()]},
            }},
        })
        try:
            return response["data"]["createCommitOnBranch"]["commit"]["oid"]
        except (KeyError, TypeError):
            raise PublishError("GitHub did not return a signed bump commit") from None

    def create_pr(self, branch: str, title: str) -> dict:
        return self.api(f"{self.path}/pulls", method="POST", label="could not open the bump PR", data={
            "head": branch, "base": self.default_branch, "title": title,
            "body": "Generated from the Brewery package manifest and verified release artifacts.",
        })

    def queue_merge(self, number: int, expected_head: str) -> None:
        self.command(
            ["pr", "merge", str(number), "--repo", self.repository, "--auto", "--merge",
             "--match-head-commit", expected_head],
            label=f"could not request auto-merge for PR #{number}", parse=False,
        )

    def verify_and_refresh(self, package: PackageResult, base: str, branch: str, head: str, number: int | None) -> str:
        origin = f"https://github.com/{self.repository}.git"
        fetch_ref = f"refs/pull/{number}/head" if number is not None else f"refs/heads/{branch}"
        git(self.root, "fetch", "--no-tags", origin, fetch_ref)
        if git(self.root, "rev-parse", "FETCH_HEAD").strip() != head:
            raise PublishError("existing branch changed during verification")
        merge_base = git(self.root, "merge-base", base, head).strip()
        changes = {
            Path(name) for name in git(self.root, "diff", "--name-only", "--no-renames", "-z", merge_base, head).split("\0")
            if name
        }
        if changes != set(package.files):
            raise PublishError("existing branch changes unexpected files")
        manifest_path, = [path for path in changes if path.suffix == ".yaml"]
        selected = yaml_parser().load(package.files[manifest_path])["channels"][package.channel]
        artifacts = ({"universal": selected["sha256"]} if "sha256" in selected
                     else {target: asset["sha256"] for target, asset in selected["artifacts"].items()})
        with tempfile.TemporaryDirectory(prefix="brewery-publisher-") as temporary:
            previous = Path(temporary) / "previous"
            git(self.root, "worktree", "add", "--detach", str(previous), merge_base)
            try:
                original = load_manifest(previous / manifest_path)
                expected = prepare_bump(original, package.channel, package.candidate, artifacts)
                actual = {path: git(self.root, "show", f"{head}:{path.as_posix()}") for path in changes}
                if expected != actual:
                    raise PublishError("existing branch does not match the verified bump")
            finally:
                git(self.root, "worktree", "remove", str(previous))
            if merge_base == base:
                return head
            return self.refresh_branch(Path(temporary), package, origin, branch, base, head)

    def refresh_branch(
        self, temporary: Path, package: PackageResult, origin: str, branch: str, base: str, old_head: str,
    ) -> str:
        checkout = temporary / "updated"
        git(self.root, "worktree", "add", "--detach", str(checkout), base)
        try:
            for path, contents in package.files.items():
                output = checkout / path
                if output.resolve() != output:
                    raise PublishError("bump output crosses a symlink")
                output.write_text(contents, encoding="utf-8", newline="\n")
            git(checkout, "add", "--", *map(str, package.files))
            tree = git(checkout, "write-tree").strip()
            # Attach the newly generated tree to both the old head and the latest base.
            commit = git(
                checkout, "-c", f"user.name={self.app_login}", "-c", "user.email=brewery@users.noreply.github.com",
                "commit-tree", tree, "-p", old_head, "-p", base, "-m", "Refresh the verified Brewery bump",
            ).strip()
            git(checkout, "reset", "--hard", base)
            ref = f"refs/heads/{branch}"
            authorization = b64encode(f"x-access-token:{os.environ['GH_TOKEN']}".encode()).decode()
            subprocess.run(
                ["git", "-C", str(checkout), "push", f"--force-with-lease={ref}:{old_head}", origin, f"{commit}:{ref}"],
                env={**os.environ, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
                     "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: Basic {authorization}"},
                check=True, capture_output=True, text=True, timeout=60,
            )
            return commit
        finally:
            git(self.root, "worktree", "remove", "--force", str(checkout))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    try:
        report = json.loads(args.report.read_text())
        base = report["base_sha"]
        repository = os.environ["GITHUB_REPOSITORY"]
        app = GitHub(root, repository, os.environ["BREWERY_APP_BOT"])
        if not FULL_SHA.fullmatch(base) or git(root, "rev-parse", "HEAD").strip() != base:
            raise PublishError("the publishing checkout does not match the scan")
        if app.get_branch_sha(app.default_branch) != base:
            raise PublishError("main moved after the scan; next run will regenerate candidates")
        packages = [result_from_json(entry) for entry in report["packages"]]
        versions = {}
        for path in sorted((root / "packages").glob("*/*.yaml")):
            data = load_manifest(path).data
            for channel, release in data["channels"].items():
                token = data["token"] + ("-pre" if channel == "pre" else "")
                versions[data["kind"], token] = release["version"]
        results = publish_bumps(app, base, packages, versions)
        args.output.write_text(json.dumps([result.__dict__ for result in results]))
    except (PublishError, ManifestError, OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        message = str(exc) if isinstance(exc, PublishError) else "could not set up package publishing"
        print(message, file=sys.stderr)
        return 1
    for result in results:
        print(f"{result.kind}:{result.token} {result.status} — {result.message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
