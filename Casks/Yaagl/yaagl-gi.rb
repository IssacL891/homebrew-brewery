cask "yaagl-gi" do
  version "0.3.8"
  sha256 "a2dcab5d67c1afc380edc9c056b233b2a2cf6738b37e40a2e4e3ef235b99cfd3"

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
