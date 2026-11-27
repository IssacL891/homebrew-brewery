# Generated from packages/casks/yaagl-hsr-os.yaml. Edit the YAML and regenerate.

cask "yaagl-hsr-os-pre" do
  version "0.4.1-alpha"
  sha256 "e2269585b46147792ca21887a93e56275c1b1d528477478bb92c6db99d46bbe4"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  conflicts_with cask: "yaagl-hsr-os"

  depends_on :macos

  app "Yaagl HSR OS.app"

  zap trash: "~/Library/Application Support/Yaagl HSR OS"
end
