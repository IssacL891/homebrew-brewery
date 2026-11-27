# Packages

## Installing packages

`brew install issacl891/brewery/<formula>`

Or `brew tap issacl891/brewery` and then `brew install <formula>`.

Or, in a `brew bundle` `Brewfile`:

```ruby
tap "issacl891/brewery"
brew "<formula>"
```

### Homebrew documentation

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

A standard manifest uses `schema: 1` and a `token` matching its filename. The optional `directory` preserves the location under `Casks/` or `Formula/`. Set the version and SHA-256 under `channels.stable` or `channels.pre`. The shared `url` supports `{version}` and `{tag}`. A channel can provide an exact URL instead. Defining both channels generates the plain token and its `-pre` counterpart with reciprocal conflicts.

Cask manifests declare the app bundle, macOS or architecture requirements, livecheck strategy, and cleanup paths. Formula manifests reference reviewed Ruby build and test code in `recipes/`. An optional patch is embedded with the recipe so the result works as standalone Homebrew Ruby. The existing `libsoil` formula stays manually maintained.

## Opt in to publishing missing binaries

Use manifest schema 2 and add a build section only for packages whose
binaries Brewery should publish. For a cask, keep the expected upstream
asset names under upstream.assets. For example, an arm64-only cask with
arch set to arm64 can use:

    schema: 2
    upstream:
      repository: example/project
      assets:
        arm64: Example-arm64.zip
    build:
      script: recipes/build-example.sh
      targets: [arm64]
      signing: none

The reviewed script receives three arguments: the source tarball pinned to the
upstream release commit, the output ZIP path, and the requested architecture.
The ZIP must contain the app bundle named in the cask. The scanner checks the
Mach-O slices and can require signature verification or notarization with
signing set to signed or notarized. A name mismatch, unavailable architecture,
or build failure leaves that package unchanged. If all expected upstream
downloads exist, the script is skipped.

For a YAML-managed source formula, use schema 2 and set build.bottle_tag to
the Homebrew tag of the targeted macOS builder, such as arm64_tahoe. CI uses
the formula's reviewed recipe and Homebrew's bottle output for that one target.
Installs on other targets can still build from source. A new target requires
a matching runner. The local act path compiles a tiny app fixture and mocks
the Homebrew bottle commands to avoid installing packages on the host.

Binary releases carry a receipt for the exact source, recipe, channel, target,
and checksum. They are staged separately from the bump PR and verified from
the public download before the PR is opened. If a prior upload is interrupted,
a matching draft can be reused. An existing asset with different bytes is left
for review. Existing packages remain on their current release routes until a
maintainer adds a build configuration.

If GitHub leaves an incomplete upload with no matching checksum, the draft
can require manual cleanup. The publisher leaves any existing asset with an
unknown or conflicting digest untouched.
