import hashlib
import hmac
import json
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
