cask "yaagl-hsr" do
  version "0.3.2"
  sha256 "eec01cc94e453c1782ff822bbe61a3b957a58337f3499f8980883189a5a4f910"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :big_sur"

  app "Yaagl HSR.app"

  zap trash: "~/Library/Application Support/Yaagl HSR"
end
