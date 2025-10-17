cask "yaagl-gi-os" do
  version "0.2.30"
  sha256 "39be6d3779ed7b0707cbb3e4a0ed2b962a8dab5e04963d5c34b9dd2337bfa88c"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
