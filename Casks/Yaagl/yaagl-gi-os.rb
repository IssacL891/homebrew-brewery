cask "yaagl-gi-os" do
  version "0.3.17"
  sha256 "e4b0c7ca19150b658d7d3d74d820b20549577422fad630df217d3e3070216aa9"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
