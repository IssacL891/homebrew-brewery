cask "yaagl-gi-os" do
  version "0.3.16"
  sha256 "2d4f9e7f827b447ea606763597520b9bcf65a9484b183eabeebfb9e5143af596"

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
