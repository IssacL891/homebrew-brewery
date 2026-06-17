cask "yaagl-gi-os" do
  version "0.3.18"
  sha256 "096aec685ddd0001f91b1d6228581b9054c01598c39d017f0b8de8bec1c46be7"

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
