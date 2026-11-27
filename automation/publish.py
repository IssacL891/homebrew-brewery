"""Publish scoped bump branches and request native GitHub auto-merge."""

import argparse
from base64 import b64encode
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import quote, urlencode

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.build_artifacts import (
    BuildError, build_identity, check_receipt, finish_candidate, public_url, publish_release, read_published, receipt_digests,
)
from automation.bumps import PackageResult, needs_binary, result_from_json
from automation.manifests import MANIFEST_DIRS, ManifestError, load_manifest, manifest_paths, yaml_parser
from automation.package_diff import candidate_digests, checksum_download, prepare_bump
from automation.pr_validation import FULL_SHA, bump_branch, git
from automation.releases import Candidate, ReleaseError, github_releases, resolve_releases, version_key


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
    if candidate is None or (not package.files and not package.build):
        raise PublishError("release candidate has no verified package diff or build")
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
        package = api.verify_package(package)
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
    if current_head and not api.owns_initial_commit(current_head):
        raise PublishError("existing branch ownership could not be verified")
    package = api.verify_package(package)
    if current_head:
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
        if package.status not in ("candidate", "built"):
            results.append(PublishResult(package.kind, package.token, package.status, package.message, "scan"))
            continue
        try:
            results.append(publish_one(api, base, package, current_versions[package.kind, package.token], open_prs))
        except (PublishError, BuildError, ManifestError, ReleaseError, OSError, subprocess.SubprocessError,
                KeyError, TypeError) as exc:
            message = str(exc) if isinstance(exc, (PublishError, BuildError)) else "could not verify or publish the candidate"
            results.append(PublishResult(package.kind, package.token, "warning", message))
    return results


CREATE_COMMIT = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid } }
}
"""


class GitHub:
    default_branch = "main"

    def __init__(self, root: Path, repository: str, app_login: str, artifacts: Path | None = None):
        self.root = root
        self.repository = repository
        self.app_login = app_login
        self.owner = repository.split("/", 1)[0]
        self.path = f"repos/{repository}"
        self.artifacts = artifacts

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

    def release(self, tag: str) -> dict | None:
        pages = self.api(f"{self.path}/releases?per_page=100", label="could not read binary releases", paginate=True)
        releases = [item for page in pages for item in page if item.get("tag_name") == tag]
        if len(releases) > 1:
            raise PublishError("more than one release uses the requested build tag")
        if not releases:
            return None
        release = releases[0]
        if (release.get("author") or {}).get("login") != self.app_login:
            raise PublishError("existing binary release has an unexpected author")
        return release

    def create_release(self, receipt: dict) -> dict:
        return self.api(f"{self.path}/releases", label="could not create draft binary release", method="POST", data={
            "tag_name": receipt["tag"], "target_commitish": git(self.root, "rev-parse", "HEAD").strip(),
            "name": f"Brewery build: {receipt['token']} {receipt['version']}",
            "body": json.dumps(receipt, sort_keys=True), "draft": True,
            "prerelease": receipt["channel"] == "pre", "make_latest": "false",
        })

    def upload(self, tag: str, path: Path) -> None:
        self.command(["release", "upload", tag, str(path), "--repo", self.repository],
                     label="could not upload the binary to its draft release", parse=False)

    def finalize(self, release_id: int) -> None:
        self.api(f"{self.path}/releases/{release_id}", method="PATCH", label="could not publish the binary release",
                 data={"draft": False, "make_latest": "false"})

    def manifest_for(self, package: PackageResult):
        base_token = package.token.removesuffix("-pre") if package.channel == "pre" else package.token
        directory = self.root / "packages" / MANIFEST_DIRS[package.kind]
        matches = [path for path in manifest_paths(self.root)
                   if path.stem == base_token and path.is_relative_to(directory)]
        if len(matches) != 1:
            raise PublishError(f"expected one manifest for {package.kind}:{base_token}")
        return load_manifest(matches[0], root=self.root)

    def expected_candidate(self, manifest, channel: str, proposed: Candidate) -> Candidate:
        data = manifest.data
        if "upstream" in data:
            policy = data["upstream"]
            found = resolve_releases(
                github_releases(policy["repository"]), policy, data["channels"][channel]["version"], channel,
                build_targets=tuple(data.get("build", {}).get("targets", ())),
            )
            if found is None or found.version != proposed.version:
                raise PublishError("the planned bump no longer matches the release policy")
            return found
        template = data.get("url", "")
        if channel != "stable" or "{version}" not in template or "{tag}" in template or version_key(proposed.version).is_prerelease:
            raise PublishError("invalid conventional release candidate")
        return Candidate(proposed.version, proposed.version,
                         {"universal": template.replace("{version}", proposed.version)})

    def verify_package(self, package: PackageResult) -> PackageResult:
        if package.build:
            return self.publish_build(package)
        manifest = self.manifest_for(package)
        expected = self.expected_candidate(manifest, package.channel, package.candidate)
        digests = candidate_digests(expected)
        if needs_binary(manifest, expected):
            _, expected, digests = read_published(manifest, package.channel, expected, self.repository, self.app_login, digests)
            if expected is None:
                raise PublishError("the previously published binary could not be verified")
        if package.candidate != expected or package.files != prepare_bump(manifest, package.channel, expected, digests):
            raise PublishError("the scan report does not match the trusted package diff")
        return package

    def publish_build(self, package: PackageResult) -> PackageResult:
        if self.artifacts is None or package.candidate is None or not package.build:
            raise PublishError("no staged binary report")
        receipt = package.build["receipt"]
        manifest = self.manifest_for(package)
        candidate = self.expected_candidate(manifest, package.channel, package.candidate)
        if candidate != package.candidate or not needs_binary(manifest, candidate):
            raise PublishError("staged binary does not match the configured release")
        digests = candidate_digests(candidate)
        if digests != package.build["digests"]:
            raise PublishError("source checksums changed before publishing")
        identity = build_identity(manifest, package.channel, candidate, digests)
        check_receipt(receipt, identity, manifest, candidate)
        tag = identity["tag"]
        finished = finish_candidate(candidate, receipt, self.repository)
        root = self.artifacts.resolve()
        files = {name: root / tag / name for name in receipt["files"]}
        if any(path.resolve() != path for path in files.values()):
            raise BuildError("staged binary path crosses a symlink")
        publish_release(self, receipt, files, lambda name: checksum_download(public_url(self.repository, tag, name)))
        prepared = prepare_bump(manifest, package.channel, finished, receipt_digests(digests, receipt))
        return replace(package, status="candidate", candidate=finished, files=prepared, build=None)

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
                original = load_manifest(previous / manifest_path, root=previous)
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
        app = GitHub(root, repository, os.environ["BREWERY_APP_BOT"], args.report.parent / "binaries")
        if not FULL_SHA.fullmatch(base) or git(root, "rev-parse", "HEAD").strip() != base:
            raise PublishError("the publishing checkout does not match the scan")
        if app.get_branch_sha(app.default_branch) != base:
            raise PublishError("main moved after the scan; next run will regenerate candidates")
        packages = [result_from_json(entry) for entry in report["packages"]]
        versions = {}
        for path in manifest_paths(root):
            data = load_manifest(path, root=root).data
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
