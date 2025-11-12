cask "yaagl-gi" do
  version "0.3.1"
  sha256 "cc477b0a4f9e528eb5512b643b534cb39d44faa3ba1213d576c74350631a7afd"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
