cask "yaagl-gi" do
  version "0.3.18"
  sha256 "5b6d8d96c445bfd1f905df57c0061153265117032b1f2ef19facbab0ad094c30"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
