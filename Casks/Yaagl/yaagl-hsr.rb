cask "yaagl-hsr" do
  version "0.3.15"
  sha256 "f31b90c03ce3a9b52b82e6ea2fde6e8fd688009e367cbef0ffbaae09e49e2cc1"

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
