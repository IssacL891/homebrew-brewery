import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.bumps import PackageResult
from automation.manifests import load_manifest
from automation.package_diff import prepare_bump
from automation.pr_validation import bump_branch, git
from automation.publish import GitHub, PublishError, publish_bumps
from automation.releases import Candidate
from automation.render import render_tree
from test_package_diff import CANDIDATE, DIGEST, MANIFEST, PRERELEASE_CASK
from test_render import DARTOTSU, PREVIEW


BASE = "a" * 40
HEAD = "b" * 40
BRANCH = "brewery-bump/cask/dartotsu/1.2.3"
PACKAGE = PackageResult(
    "cask", "dartotsu", "stable", "candidate", "1.2.3", CANDIDATE,
    {Path("packages/casks/dartotsu.yaml"): "yaml", Path("Casks/dartotsu.rb"): "ruby"},
)


class GitHubFixture:
    app_login = "brewery[bot]"
    repository = "IssacL891/homebrew-brewery"
    default_branch = "main"

    def __init__(self, open_prs=(), by_head=(), *, fail=False):
        self.open_prs = list(open_prs)
        self.by_head = list(by_head)
        self.fail = fail
        self.changes = []

    def list_open(self):
        return self.open_prs

    def find_prs(self, branch):
        return self.by_head

    def get_branch_sha(self, branch):
        return None

    def create_commit(self, branch, base, title, files):
        if self.fail:
            self.fail = False
            raise PublishError("test upload rejection")
        self.changes.append(("commit", branch, base, files))
        return HEAD

    def create_pr(self, branch, title):
        self.changes.append(("pr", branch, title))
        return {"number": 7, "html_url": "https://github.com/IssacL891/homebrew-brewery/pull/7"}

    def queue_merge(self, number, expected_head):
        self.changes.append(("merge", number, expected_head))


def pull(title, *, author="IssacL891", branch="bump-dartotsu-1.0.0", state="open"):
    return {
        "number": 3, "title": title, "state": state, "user": {"login": author},
        "head": {"ref": branch, "sha": HEAD, "repo": {"full_name": GitHubFixture.repository}},
        "base": {"ref": "main"},
    }


class PublisherTests(unittest.TestCase):
    def test_stale_legacy_pr_does_not_block_a_new_verified_bump(self):
        api = GitHubFixture(open_prs=[pull("dartotsu 1.0.0")])
        results = publish_bumps(api, BASE, [PACKAGE], {("cask", "dartotsu"): "1.0.0"})
        self.assertEqual([entry.status for entry in results], ["published"])
        self.assertEqual(api.changes, [
            ("commit", BRANCH, BASE, PACKAGE.files),
            ("pr", BRANCH, "dartotsu 1.2.3"),
            ("merge", 7, HEAD),
        ])

    def test_newer_manual_or_closed_candidate_is_left_alone(self):
        for api in (
            GitHubFixture(open_prs=[pull("dartotsu 1.1.0")]),
            GitHubFixture(by_head=[pull("dartotsu 1.2.3", state="closed", branch=BRANCH)]),
        ):
            with self.subTest(api=api):
                self.assertEqual(publish_bumps(api, BASE, [PACKAGE], {("cask", "dartotsu"): "1.0.0"})[0].status, "skipped")
                self.assertEqual(api.changes, [])

    def test_publish_error_isolated_to_a_package(self):
        other = PackageResult(
            "cask", "healthy", "stable", PACKAGE.status, PACKAGE.message, PACKAGE.candidate, PACKAGE.files,
        )
        api = GitHubFixture(fail=True)
        results = publish_bumps(api, BASE, [PACKAGE, other], {("cask", "dartotsu"): "1.0.0", ("cask", "healthy"): "1.0.0"})
        self.assertEqual([entry.status for entry in results], ["warning", "published"])

    def test_verified_orphan_is_reused_and_unknown_branch_is_left_untouched(self):
        for owned, status in ((True, "published"), (False, "warning")):
            with self.subTest(owned=owned):
                api = GitHubFixture()
                api.get_branch_sha = lambda branch: HEAD
                api.owns_initial_commit = lambda sha: owned
                api.verify_and_refresh = lambda package, base, branch, head, number: head
                result, = publish_bumps(api, BASE, [PACKAGE], {("cask", "dartotsu"): "1.0.0"})
                self.assertEqual(result.status, status)
                self.assertEqual([entry[0] for entry in api.changes], ["pr", "merge"] if owned else [])

    def test_open_app_pr_refreshes_the_head_before_retrying_auto_merge(self):
        api = GitHubFixture(by_head=[pull("dartotsu 1.2.3", author=GitHubFixture.app_login, branch=BRANCH)])
        updated = "c" * 40

        def refresh(package, base, branch, head, number):
            api.changes.append(("refresh", base, branch, head, number))
            return updated

        api.verify_and_refresh = refresh
        result, = publish_bumps(api, BASE, [PACKAGE], {("cask", "dartotsu"): "1.0.0"})
        self.assertEqual(result.status, "pending")
        self.assertEqual(api.changes, [("refresh", BASE, BRANCH, HEAD, 3), ("merge", 3, updated)])

    def test_refresh_carries_the_sibling_bump_and_rejects_a_stale_head(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch).resolve()
            repo = root / "tap"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Brewery fixture")
            git(repo, "config", "user.email", "brewery@example.invalid")
            git(repo, "config", "commit.gpgsign", "false")
            manifest = repo / MANIFEST
            manifest.parent.mkdir(parents=True)
            manifest.write_text(DARTOTSU + PREVIEW)
            render_tree(repo, check=False)
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "Base")

            pre = Candidate("1.2.3-alpha", "v1.2.3-alpha", CANDIDATE.urls)
            branch = bump_branch("cask", "dartotsu-pre", pre.version)
            git(repo, "switch", "-qc", branch)
            old = prepare_bump(load_manifest(manifest), "pre", pre, {"universal": DIGEST})
            for path, contents in old.items():
                (repo / path).write_text(contents)
            git(repo, "commit", "-qam", "Preview bump")
            old_head = git(repo, "rev-parse", "HEAD").strip()
            git(repo, "switch", "-q", "main")
            sibling = prepare_bump(load_manifest(manifest), "stable", CANDIDATE, {"universal": DIGEST})
            for path, contents in sibling.items():
                (repo / path).write_text(contents)
            git(repo, "commit", "-qam", "Merged stable bump")
            current_base = git(repo, "rev-parse", "HEAD").strip()

            remote = root / "remote.git"
            git(root, "clone", "--bare", str(repo), str(remote))
            changes = prepare_bump(load_manifest(manifest), "pre", pre, {"universal": DIGEST})
            updated = PackageResult("cask", "dartotsu-pre", "pre", "candidate", pre.version, pre, changes)
            api = GitHub(repo, "fixture/tap", GitHubFixture.app_login)

            with patch.dict("os.environ", {"GH_TOKEN": "local-test-placeholder"}):
                sha = api.refresh_branch(root, updated, str(remote), branch, current_base, old_head)
                next_head = git(
                    remote, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit-tree", f"{sha}^{{tree}}", "-p", sha, "-m", "Commit after plan publication",
                ).strip()
                git(remote, "update-ref", f"refs/heads/{branch}", next_head, sha)
                with self.assertRaises(subprocess.CalledProcessError):
                    api.refresh_branch(root, updated, str(remote), branch, current_base, old_head)
            self.assertEqual(git(remote, "rev-parse", branch).strip(), next_head)
            self.assertEqual(git(remote, "show", "-s", "--format=%P", sha).split(), [old_head, current_base])
            self.assertEqual(
                set(git(remote, "diff", "--name-only", "-z", current_base, sha).strip("\0").split("\0")),
                {str(MANIFEST), str(PRERELEASE_CASK)},
            )
            self.assertIn('version: "1.2.3"', git(remote, "show", f"{sha}:{MANIFEST}"))
            self.assertIn('version: "1.2.3-alpha"', git(remote, "show", f"{sha}:{MANIFEST}"))
