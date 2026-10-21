cask "godot-launcher" do
  version "1.13.1"
  sha256 "0c1da68e6e2d751bcf3a079d1b7fbb005a5a482b7f475605bb2073cfe213c840"

  url "https://github.com/godotlauncher/launcher/releases/download/v#{version}/Godot_Launcher-#{version}-mac_universal.dmg"
  name "godot-launcher"
  desc "Open-source launcher for Godot game development"
  homepage "https://github.com/godotlauncher/launcher"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on :macos

  app "Godot Launcher.app"
end
