"""Track actionable Brewery failures and dispatch new issues to T3 Code."""

import argparse
import hmac
import json
import logging
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.publish import GitHub


ISSUE_KEY = re.compile(r"(?:(?:cask|formula):[a-z0-9-]+:(?:scan|publish)|workflow:(?:scan|publish))\Z")
FAILURE_LINE = re.compile(r"^<!-- brewery-failure-v1:([^ ]+) ([a-z_]+) -->$", re.M)
DISPATCHED = "<!-- brewery-t3-dispatched-v1 -->"
LOG = logging.getLogger(__name__)
REASONS = {
    "asset_missing": "Expected upstream asset is missing.",
    "build_failed": "Could not build or verify the configured fallback binary.",
    "download_failed": "Could not verify the package download.",
    "discovery_failed": "Could not identify a usable upstream release.",
    "publication_failed": "Could not publish or queue the bump.",
    "workflow_blocked": "The workflow step did not complete.",
}


def app_owned(item: dict, app_login: str) -> bool:
    return (item.get("user") or {}).get("login") == app_login


def open_failures(api: GitHub) -> dict:
    pages = api.api(f"{api.path}/issues?state=open&per_page=100",
                    paginate=True, label="could not read open Brewery issues")
    failures = {}
    for page in pages:
        for issue in page:
            if "pull_request" in issue or not app_owned(issue, api.app_login):
                continue
            match = FAILURE_LINE.search(issue.get("body") or "")
            if match and ISSUE_KEY.fullmatch(match[1]) and match[2] in REASONS:
                failures[match[1], match[2]] = issue
    return failures


def create_issue(api: GitHub, key: str, reason: str, run: str) -> dict:
    return api.api(f"{api.path}/issues", method="POST", label="could not create Brewery issue", data={
        "title": f"Brewery failure — {key} ({reason})",
        "body": f"{REASONS[reason]}\n\n[Workflow run]({run})\n\n"
                f"<!-- brewery-failure-v1:{key} {reason} -->",
    })


def report_failures(api: GitHub, observations: dict, run: str, deliver) -> None:
    failures = open_failures(api)
    for key, reason in sorted(observations.items()):
        if reason is None:
            continue
        existing = failures.get((key, reason))
        issue = existing or create_issue(api, key, reason, run)
        number = issue["number"]
        target = f"{api.path}/issues/{number}/comments"
        if existing and existing.get("comments"):
            pages = api.api(f"{target}?per_page=100", paginate=True, label="could not read T3 receipt")
            if any(comment["body"] == DISPATCHED and app_owned(comment, api.app_login)
                   for page in pages for comment in page):
                continue
        try:
            deliver(number)
            api.api(target, method="POST", data={"body": DISPATCHED}, label="could not record T3 receipt")
        except (OSError, ValueError):
            LOG.warning("Brewery issue #%s has no recorded T3 receipt. A later scan will retry.", number)

    for (key, _), issue in failures.items():
        if key in observations and observations[key] is None:
            api.api(f"{api.path}/issues/{issue['number']}", method="PATCH",
                    data={"state": "closed", "state_reason": "completed"},
                    label="could not close recovered Brewery issue")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def dispatch_to_t3(url: str, secret: str, repository: str, number: int) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or not secret:
        raise ValueError("T3 HTTPS URL and signing secret are required")
    payload = json.dumps({"repository": repository, "issue": number}).encode()
    digest = hmac.digest(secret.encode(), payload, "sha256").hex()
    request = Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={digest}",
    })
    with build_opener(NoRedirect()).open(request, timeout=20) as response:
        outcome = response.headers.get("X-T3-Hook-Outcome")
        if response.status != 202 or outcome not in {"accepted", "duplicate"}:
            raise OSError("T3 did not accept the repair request")


def scan_reason(message: str) -> str:
    if message.startswith("binary build:"):
        return "build_failed"
    if message.startswith("missing release asset"):
        return "asset_missing"
    if message.startswith(("download", "package download")):
        return "download_failed"
    return "discovery_failed"


def observations_from_reports(scan: Path, publish: Path, scan_status: str, publish_status: str) -> dict:
    observations = {}
    for role, path, status in (("scan", scan, scan_status), ("publish", publish, publish_status)):
        workflow_key = f"workflow:{role}"
        if status != "success" or not path.is_file():
            if status != "skipped":
                observations[workflow_key] = "workflow_blocked"
            continue
        observations[workflow_key] = None
        data = json.loads(path.read_text())
        rows = data["packages"] if role == "scan" else data
        for item in rows:
            key = f"{item['kind']}:{item['token']}:{role}"
            if not ISSUE_KEY.fullmatch(key):
                continue
            if role == "publish" and item.get("stage") == "scan" and item["status"] == "warning":
                continue
            reason = scan_reason(item["message"]) if role == "scan" else "publication_failed"
            observations[key] = reason if item["status"] == "warning" else None
    return observations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--publish", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(format="::warning::%(message)s")
    try:
        repo = os.environ["GITHUB_REPOSITORY"]
        app_login = os.environ["BREWERY_APP_BOT"]
        run = int(os.environ["GITHUB_RUN_ID"])
        if run < 1 or not app_login.endswith("[bot]"):
            raise ValueError("invalid Brewery notification settings")
        api = GitHub(Path.cwd(), repo, app_login)
        observations = observations_from_reports(
            args.scan, args.publish, os.environ["SCAN_STATUS"], os.environ["PUBLISH_STATUS"],
        )
        url = os.environ.get("BREWERY_T3_WEBHOOK_URL", "")
        secret = os.environ.get("BREWERY_T3_WEBHOOK_SECRET", "")
        report_failures(
            api, observations, f"https://github.com/{repo}/actions/runs/{run}",
            lambda issue: dispatch_to_t3(url, secret, repo, issue),
        )
    except (OSError, ValueError, KeyError):
        LOG.warning("Brewery could not finish reporting failures. The next scheduled run will reconcile issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
