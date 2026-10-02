cask "godot-launcher" do
  version "1.9.0"
  sha256 "26451a1e9c9e60bca46b7f666c90f465b629f7efa77dcb873a18c103e67ce4ef"

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
