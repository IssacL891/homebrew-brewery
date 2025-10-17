cask "yaagl-gi" do
  version "0.2.30"
  sha256 "1f4010d1ffc13f2ac33a17d02fa6392236ae6861c948419211001f5bf799f405"

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
