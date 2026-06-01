cask "yaagl-gi" do
  version "0.3.16"
  sha256 "434054f8e00303e3a43fe081153038d3b7eb4cc80acfabd7d4a23c89993e1573"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
