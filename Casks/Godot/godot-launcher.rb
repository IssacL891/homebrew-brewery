cask "godot-launcher" do
  version "1.12.0"
  sha256 "580be3b588b55295ade6c4af3a8a4f9fc090ee56ebd6ca7576990fdbadd59349"

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
