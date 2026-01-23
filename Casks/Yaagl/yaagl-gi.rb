cask "yaagl-gi" do
  version "0.3.7"
  sha256 "ec3fa7fcff7abf18275352b83e58e7401b2361488adceea4fdf10582d9c3f7ab"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :big_sur"

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
