# Generated from packages/casks/Yaagl/yaagl-hsr-os.yaml. Edit the YAML and regenerate.

cask "yaagl-hsr-os" do
  version "0.4.0"
  sha256 "ce71055e881db9ccbbbab7b9804f754b7187a779bc5ab3556480c56cf00f30d4"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  conflicts_with cask: "yaagl-hsr-os-pre"

  depends_on :macos

  app "Yaagl HSR OS.app"

  zap trash: "~/Library/Application Support/Yaagl HSR OS"
end
