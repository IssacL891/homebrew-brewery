cask "yaagl-gi" do
  version "0.3.20"
  sha256 "3ad44962467b65d9ab8a3be1ffaff9a382a4dea82ca754fb7ef442a7895d5a2f"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
