cask "yaagl-hsr" do
  version "0.3.0"
  sha256 "d151551ce83083e56adbb4fb71780cde48a5fbbab4df68c5cd4e1bb9f96c7191"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl HSR.app"

  zap trash: "~/Library/Application Support/Yaagl HSR"
end
