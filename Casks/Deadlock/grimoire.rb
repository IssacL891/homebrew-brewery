cask "grimoire" do
  version "1.31.0"
  sha256 "e2c9fda83b92ceccc36e5d4dd4eb9f7b844a50e6ab4277a6f4780cb53fcd4496"

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
