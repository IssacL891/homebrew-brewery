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

    def test_three_reports_post_only_initial_failure_and_recovery(self):
        import json
        from pathlib import Path
        import tempfile
        from unittest.mock import patch

        from automation.notifications import main

        with tempfile.TemporaryDirectory() as temporary:
            scan = Path(temporary) / "scan.json"
            publish = Path(temporary) / "publish.json"
            comments = []

            def api(endpoint, *, label, data=None, **unused):
                if data is None:
                    return [list(comments)]
                comments.append({"user": {"login": APP}, "body": data["body"]})
                return {}

            context = {
                "BREWERY_ISSUE_NUMBER": "5", "GITHUB_REPOSITORY": "IssacL891/homebrew-brewery",
                "BREWERY_APP_BOT": APP, "GITHUB_RUN_ID": "10", "SCAN_STATUS": "success",
                "PUBLISH_STATUS": "skipped",
            }
            with (
                patch.dict("os.environ", context),
                patch("sys.argv", ["notifications.py", "--scan", str(scan), "--publish", str(publish)]),
                patch("automation.notifications.GitHub.api", side_effect=api),
            ):
                for status in ("warning", "warning", "current"):
                    scan.write_text(json.dumps({"packages": [{
                        "kind": "cask", "token": "dartotsu", "status": status,
                        "message": "missing release asset for universal",
                    }]}))
                    self.assertEqual(main(), 0)
            self.assertEqual(len(comments), 2)
            self.assertIn("Needs attention", comments[0]["body"])
            self.assertIn("Cleared", comments[1]["body"])
