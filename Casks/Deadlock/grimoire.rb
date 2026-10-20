cask "grimoire" do
  version "1.33.0"
  sha256 "eccb980708827a07a3bdaadcb76ce2c8a821a51f149ef4422d2c5eae59480305"

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
