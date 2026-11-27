import unittest

from automation.notifications import compare_issues, format_comment, read_issue_state


DARTOTSU = "cask:dartotsu:scan"
PUBLISH = "cask:yaagl-gi:publish"
APP = "brewery[bot]"
FAILED = {"code": "asset_missing"}
BLOCKER = {"code": "workflow_blocked"}


class NotificationsTests(unittest.TestCase):
    def test_new_repeated_and_recovered_failure(self):
        first = compare_issues({}, {DARTOTSU: FAILED}, complete=True)
        self.assertEqual(first, {DARTOTSU: FAILED})
        self.assertIsNone(compare_issues(first, {DARTOTSU: FAILED}, complete=True))
        self.assertEqual(compare_issues(first, {DARTOTSU: None}, complete=True), {})

    def test_partial_scan_does_not_clear_unobserved_failure(self):
        self.assertIsNone(compare_issues({DARTOTSU: FAILED}, {PUBLISH: None}, complete=False))
        self.assertEqual(
            compare_issues({DARTOTSU: FAILED}, {"workflow:scan": BLOCKER}, complete=False),
            {DARTOTSU: FAILED, "workflow:scan": BLOCKER},
        )

    def test_read_state_uses_only_expected_app_comments(self):
        state = {DARTOTSU: FAILED}
        run = "https://github.com/IssacL891/homebrew-brewery/actions/runs/123"
        original = format_comment({}, state, run)
        forged = format_comment(state, {}, run)
        comments = [
            {"user": {"login": APP}, "body": original},
            {"user": {"login": "other[bot]"}, "body": forged},
            {"user": {"login": APP}, "body": "ordinary comment without state"},
        ]
        self.assertEqual(read_issue_state(comments, APP), state)

    def test_comment_contains_only_vetted_reason_and_run_link(self):
        run = "https://github.com/IssacL891/homebrew-brewery/actions/runs/123"
        text = format_comment({PUBLISH: BLOCKER}, {DARTOTSU: FAILED}, run)
        self.assertIn("Expected upstream asset is missing", text)
        self.assertIn("yaagl-gi", text)
        self.assertIn(run, text)
        self.assertIn("Cleared", text)
