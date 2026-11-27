# IssacL891 Brewery

## How do I install these formulae?

`brew install issacl891/brewery/<formula>`

Or `brew tap issacl891/brewery` and then `brew install <formula>`.

Or, in a `brew bundle` `Brewfile`:

```ruby
tap "issacl891/brewery"
brew "<formula>"
```

## Documentation

`brew help`, `man brew` or check [Homebrew's documentation](https://docs.brew.sh).

## Maintaining packages

Edit the YAML for a managed package in `packages/casks/` or `packages/formulae/`. Generate the Homebrew definitions and commit the YAML and generated Ruby together.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r automation/requirements.txt
.venv/bin/python automation/render.py
.venv/bin/python automation/render.py --check
.venv/bin/python -m unittest discover -s tests -v
```

Each manifest uses `schema: 1` and a `token` matching its filename. The optional `directory` preserves the location under `Casks/` or `Formula/`. Set the version and SHA-256 under `channels.stable` or `channels.pre`. The shared `url` supports `{version}` and `{tag}`. A channel can provide an exact URL instead. Defining both channels generates the plain token and its `-pre` counterpart with reciprocal conflicts.

Cask manifests declare the app bundle, macOS or architecture requirements, livecheck strategy, and cleanup paths. Formula manifests reference reviewed Ruby build and test code in `recipes/`. An optional patch is embedded with the recipe so the result works as standalone Homebrew Ruby. The existing `libsoil` formula stays manually maintained.

### Yaagl release channels

The six existing Yaagl cask names track stable releases. Install the corresponding
name ending in -pre to follow prereleases. Homebrew treats each stable and
prerelease pair as conflicting packages.

Five of the stable-named casks previously pointed at 0.4.1-alpha. The first
channel split pins them to 0.4.0 stable. A normal brew upgrade can move those
installs from the alpha back to stable. To keep using the alpha, switch to the
matching -pre cask. For example, for Yaagl GI OS:

    brew uninstall --cask issacl891/brewery/yaagl-gi-os
    brew install --cask issacl891/brewery/yaagl-gi-os-pre

Use the same commands with the token for your edition. The uninstall command
above preserves the application data that the cask removes only when asked
to zap.

## Update workflow

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
