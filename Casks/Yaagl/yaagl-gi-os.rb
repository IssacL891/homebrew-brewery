cask "yaagl-gi-os" do
  version "0.4.0"
  sha256 "1c7a9c41e0b7d26eb0c776cd9f70ee41920a5bb05749fd24d84224a71a00b89b"

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
