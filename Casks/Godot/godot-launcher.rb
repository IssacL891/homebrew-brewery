cask "godot-launcher" do
  version "1.13.0"
  sha256 "ef3c5cd24cc9d5c9bddcad057e456dd4f1a494ecdf183402d5ad79ddcfcb158b"

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
