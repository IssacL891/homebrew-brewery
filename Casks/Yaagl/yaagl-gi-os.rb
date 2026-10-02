cask "yaagl-gi-os" do
  version "0.3.20"
  sha256 "221f053e773d4513cf087f3b63616916f3c1db7b315fe7098bdec1947770eab6"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
