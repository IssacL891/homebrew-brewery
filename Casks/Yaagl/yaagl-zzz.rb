cask "yaagl-zzz" do
  version "0.3.16"
  sha256 "9ab8a536cacdc07dd05974eb5c32c4a0dfe96f8f573d13552c1f1669e1759d33"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl ZZZ.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ"
end
