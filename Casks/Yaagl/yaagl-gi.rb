cask "yaagl-gi" do
  version "0.3.10"
  sha256 "d532f9b9373d50a143cb0e571545d3cf7679550438f5c03a5468ee211f133ac1"

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
