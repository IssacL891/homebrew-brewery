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
