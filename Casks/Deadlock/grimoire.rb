cask "grimoire" do
  version "1.29.0"
  sha256 "56601b8f0721fd21bedc889d9bf6a25b64eaa399dd73d96676a1154e9ad7ed39"

  url "https://github.com/Slush97/grimoire/releases/download/v#{version}/Grimoire-#{version}-arm64.dmg"
  name "Grimoire"
  desc "Mod manager and companion tool for Deadlock"
  homepage "https://github.com/Slush97/grimoire"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on arch: :arm64

  app "Grimoire.app"
end
