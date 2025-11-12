cask "yaagl-gi-os" do
  version "0.3.1"
  sha256 "b003db97f8efbb4839b3edd098cb7f410813aaf9370aca1de4899b40ba457201"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :big_sur"

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
