"""Report only transitions in actionable package failures to a subscribed issue."""

import argparse
import json
import os
from pathlib import Path
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.publish import GitHub


ISSUE_KEY = re.compile(r"(?:(?:cask|formula):[a-z0-9-]+:(?:scan|publish)|workflow:(?:scan|publish))\Z")
STATE_LINE = re.compile(r"^<!-- brewery-state-v1:(.+) -->$", re.M)
REASONS = {
    "asset_missing": "Expected upstream asset is missing.",
    "build_failed": "Could not build or verify the configured fallback binary.",
    "download_failed": "Could not verify the package download.",
    "discovery_failed": "Could not identify a usable upstream release.",
    "publication_failed": "Could not publish or queue the bump.",
    "workflow_blocked": "The workflow step did not complete.",
}


def compare_issues(previous: dict, observations: dict, complete: bool) -> dict | None:
    state = {key: status for key, status in previous.items() if not complete or key in observations}
    for key, status in observations.items():
        if status is None:
            state.pop(key, None)
        else:
            state[key] = status
    return state if state != previous else None


def format_comment(previous: dict, state: dict, run: str) -> str:
    lines = ["Brewery automation report", "", f"[Workflow run]({run})"]
    new = {key: value for key, value in state.items() if previous.get(key) != value}
    if new:
        lines.extend(["", "**Needs attention**", ""])
        lines.extend(f"- {key} — {REASONS[value['code']]}" for key, value in sorted(new.items()))
    cleared = previous.keys() - state.keys()
    if cleared:
        lines.extend(["", "**Cleared**", ""])
        lines.extend(f"- {key}" for key in sorted(cleared))
    lines.extend(["", f"<!-- brewery-state-v1:{json.dumps(state, sort_keys=True, separators=(',', ':'))} -->"])
    return "\n".join(lines)


def valid_state(state) -> bool:
    return isinstance(state, dict) and all(
        isinstance(key, str) and ISSUE_KEY.fullmatch(key)
        and isinstance(value, dict) and set(value) == {"code"}
        and isinstance(value["code"], str) and value["code"] in REASONS
        for key, value in state.items()
    )


def read_issue_state(comments: list[dict], app_login: str) -> dict:
    for comment in reversed(comments):
        if (comment.get("user") or {}).get("login") != app_login:
            continue
        match = STATE_LINE.search(comment.get("body") or "")
        if match:
            try:
                state = json.loads(match[1])
            except json.JSONDecodeError:
                continue
            if valid_state(state):
                return state
    return {}


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
                observations[workflow_key] = {"code": "workflow_blocked"}
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
            observations[key] = {"code": reason} if item["status"] == "warning" else None
    return observations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--publish", type=Path, required=True)
    args = parser.parse_args()
    try:
        issue = int(os.environ["BREWERY_ISSUE_NUMBER"])
        repo = os.environ["GITHUB_REPOSITORY"]
        app_login = os.environ["BREWERY_APP_BOT"]
        run = int(os.environ["GITHUB_RUN_ID"])
        if issue < 1 or run < 1 or not app_login.endswith("[bot]"):
            raise ValueError("invalid Brewery notification settings")
        api = GitHub(Path.cwd(), repo, app_login)
        target = f"{api.path}/issues/{issue}/comments"
        pages = api.api(f"{target}?per_page=100", paginate=True, label="could not read tracking issue")
        previous = read_issue_state([comment for page in pages for comment in page], app_login)
        observations = observations_from_reports(
            args.scan, args.publish, os.environ["SCAN_STATUS"], os.environ["PUBLISH_STATUS"],
        )
        # Unobserved packages cannot be marked as recovered.
        state = compare_issues(previous, observations, complete=False)
        if state is not None:
            body = format_comment(previous, state, f"https://github.com/{repo}/actions/runs/{run}")
            api.api(target, method="POST", data={"body": body}, label="could not update the tracking issue")
    except (OSError, ValueError, KeyError):
        print("::warning::Brewery could not update its tracking issue. The next scheduled run will retry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
