# Package update workflow

Run a read-only update scan locally with:

    .venv/bin/python automation/bumps.py scan --dry-run
    .venv/bin/python automation/bumps.py scan --dry-run --package cask:dartotsu

A scan looks for newer candidates, verifies the selected artifacts, and prints
the proposed YAML and Ruby diff. Tap-wide scans continue and report isolated
package errors. A failed validation check blocks that pull request.

The scheduled GitHub workflow also starts in scan mode. Before enabling
publication, pause the legacy scheduler and turn off repository auto-merge.
Review existing queued merges and the three legacy bump PRs #192, #194, and
#202. Keep the existing required check until the new check runs successfully,
then replace it with the strict, Actions-sourced package-validation check.
Review the active ruleset alongside classic branch protection. Retire the
legacy approval workflow, default the Actions token to read-only, and disable
automatic PR reviews.

Install a dedicated GitHub App on this tap with contents, pull requests, and
issues write permissions. Set BREWERY_APP_CLIENT_ID and BREWERY_APP_BOT as
repository variables and BREWERY_APP_PRIVATE_KEY as an Actions secret. Restore
GitHub auto-merge and set BREWERY_PUBLISH_ENABLED to true only after the required
check is in force. Confirm an app PR has no bypass and stays open when the
check fails.

To receive alerts, configure BREWERY_ISSUE_NUMBER for one tracking issue and
subscribe to it. The reporter uses an issues-only token and posts only when the
recorded problems change. GitHub delivers those updates using your notification
settings.

## Cutover and rollback

Keep the original GitHub branch protection, ruleset, workflow settings, and
legacy workflow states recorded before cutover. To pause publication, unset
BREWERY_PUBLISH_ENABLED and turn off native auto-merge while inspecting
queued PRs. Keep the current required check in place during a rollback until
its replacement has been demonstrated. Restore the previous settings only
after confirming that open PRs and scheduled workflows are safe to resume.
