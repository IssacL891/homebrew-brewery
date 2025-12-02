cask "yaagl-gi-os" do
  version "0.3.3"
  sha256 "ce0a074b1a7f9368cd3990418ed99c79a24f3fe665e5bbd276ae1f92becee266"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :big_sur"

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
