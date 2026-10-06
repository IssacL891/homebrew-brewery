cask "yaagl-gi" do
  version "0.3.21"
  sha256 "1466f47525c108bd8021c0f0cef309e92a09b4adadb5584ffe10066d9e548944"

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
