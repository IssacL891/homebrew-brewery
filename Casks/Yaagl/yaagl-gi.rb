cask "yaagl-gi" do
  version "0.3.3"
  sha256 "b11a916236c3100ffaf10a10814a5d4b7ddf58b431afba55f9e2b5b6338b6c68"

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
