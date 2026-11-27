# Generated from packages/casks/yaagl-hsr.yaml. Edit the YAML and regenerate.

cask "yaagl-hsr" do
  version "0.4.0"
  sha256 "1f3d3ca8d7b0d7d340d9dd79e0d3a33e0386f022fecaa75dfe1b9d2becbfac6e"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  conflicts_with cask: "yaagl-hsr-pre"

  depends_on :macos

  app "Yaagl HSR.app"

  zap trash: "~/Library/Application Support/Yaagl HSR"
end
