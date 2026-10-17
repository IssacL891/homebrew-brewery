cask "grimoire" do
  version "1.32.0"
  sha256 "44eed9c53927fa0554047a12583eaf475e23345137ba4b2ae0fc80f2086e3be9"

  url "https://github.com/Slush97/grimoire/releases/download/v#{version}/Grimoire-#{version}-arm64.dmg"
  name "Grimoire"
  desc "Mod manager and companion tool for Deadlock"
  homepage "https://github.com/Slush97/grimoire"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on arch: :arm64
  depends_on :macos

  app "Grimoire.app"
end
