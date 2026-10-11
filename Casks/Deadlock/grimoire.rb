cask "grimoire" do
  version "1.31.5"
  sha256 "d402c0e3a89ef6181fe88888dafcc8366198793ef900332ff7f19008b46bc97b"

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
