import hashlib
import hmac
import json
from http.client import BadStatusLine
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from automation import notifications


REPO = "IssacL891/homebrew-brewery"
RUN = f"https://github.com/{REPO}/actions/runs/123"
APP = "brewery[bot]"
PACKAGE = "cask:dartotsu:scan"
REASON = "asset_missing"


class IssueApi:
    app_login = APP
    path = f"repos/{REPO}"
    repository = REPO

    def __init__(self):
        self.issues = []

    def api(self, endpoint, *, method="GET", data=None, **kwargs):
        path = endpoint.removeprefix(f"{self.path}/issues")
        if method == "POST" and not path:
            issue = {**data, "number": len(self.issues) + 1, "state": "open",
                     "user": {"login": APP}, "comments": []}
            self.issues.append(issue)
            return issue
        if path.startswith("?"):
            return [[issue for issue in self.issues if issue["state"] == "open"]]
        issue = self.issues[int(path.split("/")[1].split("?")[0]) - 1]
        if method == "PATCH":
            issue.update(data)
        elif method == "POST":
            issue["comments"].append({"user": {"login": APP}, "body": data["body"]})
        else:
            return [issue["comments"]]
        return {}


class NotificationsTests(unittest.TestCase):
    def test_creates_one_issue_and_delivers_once_until_recovery(self):
        api, deliver = IssueApi(), Mock()
        notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        self.assertEqual(len(api.issues), 1)
        deliver.assert_called_once_with(1)
        self.assertIn(RUN, api.issues[0]["body"])
        self.assertIn("Expected upstream asset is missing", api.issues[0]["body"])
        notifications.report_failures(api, {}, RUN, deliver)
        self.assertEqual(api.issues[0]["state"], "open")
        notifications.report_failures(api, {PACKAGE: None}, RUN, deliver)
        self.assertEqual(api.issues[0]["state"], "closed")
        notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        self.assertEqual(len(api.issues), 2)

    def test_changed_reason_closes_superseded_issue_then_recovers(self):
        api, deliver = IssueApi(), Mock()
        notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        notifications.report_failures(api, {PACKAGE: "download_failed"}, RUN, deliver)
        self.assertEqual(api.issues[0]["state"], "closed")
        self.assertEqual(api.issues[0]["state_reason"], "not_planned")
        self.assertEqual(api.issues[1]["state"], "open")
        notifications.report_failures(api, {PACKAGE: None}, RUN, deliver)
        self.assertEqual(api.issues[1]["state"], "closed")
        self.assertEqual(api.issues[1]["state_reason"], "completed")

    def test_bad_http_response_does_not_block_other_issues(self):
        api, deliver = IssueApi(), Mock(side_effect=[BadStatusLine("sensitive"), None])
        with self.assertLogs("automation.notifications", level="WARNING") as log:
            notifications.report_failures(api, {PACKAGE: REASON, "workflow:publish": "workflow_blocked"},
                                          RUN, deliver)
        self.assertNotIn("sensitive", str(log.output))
        self.assertEqual(deliver.call_count, 2)
        self.assertEqual(api.issues[0]["comments"], [])
        self.assertEqual(len(api.issues[1]["comments"]), 1)

    def test_retries_dispatch_without_creating_a_new_issue(self):
        api, deliver = IssueApi(), Mock(side_effect=[OSError("sensitive URL"), None])
        with self.assertLogs("automation.notifications", level="WARNING") as log:
            notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        self.assertNotIn("sensitive URL", str(log.output))
        notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        self.assertEqual([call.args for call in deliver.call_args_list], [(1,), (1,)])
        self.assertEqual(len(api.issues), 1)

    def test_distinct_failures_get_separate_issues_and_forged_markers_are_ignored(self):
        api, deliver = IssueApi(), Mock()
        notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        api.issues[0]["user"]["login"] = "other"
        notifications.report_failures(api, {PACKAGE: REASON, "workflow:publish": "workflow_blocked"}, RUN, deliver)
        self.assertEqual(len(api.issues), 3)
        self.assertEqual(deliver.call_count, 3)
        api.issues[1]["comments"][0]["user"]["login"] = "other"
        notifications.report_failures(api, {PACKAGE: REASON}, RUN, deliver)
        self.assertEqual(deliver.call_args.args, (2,))
        self.assertEqual(deliver.call_count, 4)

    def test_reports_vetted_codes_and_partial_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            scan = Path(temporary) / "scan.json"
            publish = Path(temporary) / "publish.json"
            scan.write_text(json.dumps({"packages": [{
                "kind": "cask", "token": "dartotsu", "status": "warning",
                "message": "missing release asset with a sensitive URL",
            }]}))
            self.assertEqual(
                notifications.observations_from_reports(scan, publish, "success", "failure"),
                {"workflow:scan": None, PACKAGE: REASON, "workflow:publish": "workflow_blocked"},
            )

    def test_cancelled_jobs_and_skipped_publishes_leave_prior_state_unobserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            scan = Path(temporary) / "scan.json"
            publish = Path(temporary) / "publish.json"
            publish.write_text(json.dumps([{
                "kind": "cask", "token": "dartotsu", "status": "skipped",
                "message": "pending candidate in PR #123",
            }]))
            self.assertEqual(notifications.observations_from_reports(scan, publish, "cancelled", "success"),
                             {"workflow:publish": None})

    def test_cli_opens_issue_and_warns_when_t3_is_unconfigured(self):
        api = IssueApi()
        with tempfile.TemporaryDirectory() as temporary:
            scan = Path(temporary) / "scan.json"
            publish = Path(temporary) / "publish.json"
            env = {"GITHUB_REPOSITORY": REPO, "BREWERY_APP_BOT": APP, "GITHUB_RUN_ID": "123",
                   "SCAN_STATUS": "failure", "PUBLISH_STATUS": "skipped"}
            with (
                patch.dict("os.environ", env, clear=True),
                patch("sys.argv", ["notifications.py", "--scan", str(scan), "--publish", str(publish)]),
                patch.object(notifications, "GitHub", return_value=api),
                self.assertLogs("automation.notifications", level="WARNING") as log,
            ):
                self.assertEqual(notifications.main(), 0)
        self.assertIn("no recorded T3 receipt", log.output[0])
        self.assertEqual(len(api.issues), 1)
        self.assertIn(RUN, api.issues[0]["body"])
        self.assertEqual(api.issues[0]["comments"], [])

    def test_dispatch_signs_minimal_json_and_checks_receipt(self):
        response = Mock(status=202, headers={"X-T3-Hook-Outcome": "accepted"})
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = response
        with patch.object(notifications, "build_opener", return_value=opener):
            notifications.dispatch_to_t3("https://example.com/receiver", "shared", REPO, 17)
            request = opener.open.call_args.args[0]
            self.assertEqual(json.loads(request.data), {"repository": REPO, "issue": 17})
            digest = hmac.new(b"shared", request.data, hashlib.sha256).hexdigest()
            self.assertEqual(request.get_header("X-hub-signature-256"), f"sha256={digest}")
            response.headers["X-T3-Hook-Outcome"] = "filtered"
            with self.assertRaises(OSError):
                notifications.dispatch_to_t3("https://example.com/receiver", "shared", REPO, 17)

    def test_t3_connect_relay_receipt_has_delivery_id_without_outcome_header(self):
        response = Mock(status=202, headers={})
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"deliveryId":"relay-delivery-17"}'
        opener = Mock()
        opener.open.return_value = response
        with patch.object(notifications, "build_opener", return_value=opener):
            notifications.dispatch_to_t3("https://example.com/receiver", "shared", REPO, 17)
            response.read.return_value = b'{"status":"unexpected"}'
            with self.assertRaises(OSError):
                notifications.dispatch_to_t3("https://example.com/receiver", "shared", REPO, 17)
