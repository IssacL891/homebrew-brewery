cask "yaagl-gi" do
  version "0.3.0"
  sha256 "8cb616f978b750483ce7d8b69897e7cc5f31b4fde0762a3bf87529d07021f5c0"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
