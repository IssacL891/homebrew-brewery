cask "yaagl-gi-os" do
  version "0.3.21"
  sha256 "8a3fcedc5eac8d4917c51d6f8c2ab54f90112dcdbb6ad401ee93567ae8a6ad01"

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
