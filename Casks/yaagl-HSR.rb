cask "yaagl-hsr" do
  version "0.2.26"
  sha256 "1b3f14ebd7683eff934a4dd38c46ba6f6c9b0298c8282379a0473a6c3c956f78"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "A launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "Yaagl HSR.app"

  zap trash: [
    "~/Library/Application Support/Yaagl HSR"
]
end
