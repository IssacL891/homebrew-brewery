# Generated from packages/casks/Yaagl/yaagl-gi-os.yaml. Edit the YAML and regenerate.

cask "yaagl-gi-os-pre" do
  version "0.4.1-alpha"
  sha256 "61f86caef043fe8cbf1438d207092392c6aa5ddff6688a853afcf8dc0318302d"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  conflicts_with cask: "yaagl-gi-os"

  depends_on :macos

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
