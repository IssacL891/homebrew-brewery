cask "yaagl-gi" do
  version "0.4.0"
  sha256 "7d8be6ace5161d061e8f8e9839f5f18ee2dc7e86a0f529e2d197f53697881687"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
