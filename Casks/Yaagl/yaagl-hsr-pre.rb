# Generated from packages/casks/yaagl-hsr.yaml. Edit the YAML and regenerate.

cask "yaagl-hsr-pre" do
  version "0.4.1-alpha"
  sha256 "c293e5a5a759246ed9ffa7fb97665b9b061c45adb1912ed81ded0305fdecc74b"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  conflicts_with cask: "yaagl-hsr"

  depends_on :macos

  app "Yaagl HSR.app"

  zap trash: "~/Library/Application Support/Yaagl HSR"
end
