cask "yaagl-hsr" do
  version "0.3.16"
  sha256 "766febe5ac9260d4f269041425b9cb7b773cfd28c304d5bca5e039b1efbe8533"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl HSR.app"

  zap trash: "~/Library/Application Support/Yaagl HSR"
end
