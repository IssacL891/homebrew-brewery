cask "yaagl-zzz" do
  version "0.2.30"
  sha256 "b28ad1ff502dee1339537104afd427e557dc3eb666777752a05170526209eb62"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl ZZZ.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ"
end
