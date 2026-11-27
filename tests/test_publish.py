import unittest
from pathlib import Path

from automation.bumps import PackageResult
from automation.publish import PublishError, publish_bumps
from test_package_diff import CANDIDATE


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
