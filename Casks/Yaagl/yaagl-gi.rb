cask "yaagl-gi" do
  version "0.3.4"
  sha256 "1d4a824d6c0762d09a34c2cefe8d66ebb4aa357edd0b15d237d7b0c3601000fd"

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
