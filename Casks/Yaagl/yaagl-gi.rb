cask "yaagl-gi" do
  version "0.2.29"
  sha256 "d08b1a0a0ca19b03af6605e0ac8304e4cdd04d0047e8aa57b3d5857ca0d3e1d3"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
