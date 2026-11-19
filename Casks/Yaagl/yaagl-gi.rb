cask "yaagl-gi" do
  version "0.4.1-alpha"
  sha256 "aea86fc7e55f18e0aeacf7954f7dc17ae54236a9bb8782fd04a7484b34fcc14a"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
