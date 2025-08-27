cask "yaggl-gi" do
  version "0.2.26"
  sha256 "6a4117a8dbdae6a377ece0a2f493d9b544b7a9f32833e57a65f99734d1b2b8c4"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "A launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on macos: ""

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
