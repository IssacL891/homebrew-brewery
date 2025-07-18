cask "yaagl-gi-os" do
  version "0.2.26"
  sha256 "9bd3221ac1ee9ed7017643dce4a5cbe6e4ea55186d84ee0661dec3e2632af9b1"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "A launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "Yaagl OS.app"

    zap trash: [
    "~/Library/Application Support/Yaagl OS"
]
end
