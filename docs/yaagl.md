# Yaagl release channels

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
