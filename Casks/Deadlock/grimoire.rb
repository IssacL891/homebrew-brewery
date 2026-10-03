cask "grimoire" do
  version "1.30.1"
  sha256 "c67fdf3905ba9734b8b6a3bdd5918a8452a5f25a8417e8553d52f57b0b830fcd"

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
