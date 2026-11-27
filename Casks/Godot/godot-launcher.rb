# Generated from packages/casks/Godot/godot-launcher.yaml. Edit the YAML and regenerate.

cask "godot-launcher" do
  version "1.14.0"
  sha256 "5ba1dc3c8788290a75c2da5c3f352593c7ca287caeec98d703f2ad38ddf247b3"

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
