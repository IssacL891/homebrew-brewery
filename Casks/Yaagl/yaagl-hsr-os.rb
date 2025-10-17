cask "yaagl-hsr-os" do
  version "0.2.30"
  sha256 "92ec83a2fb77692bffeb95c79048286aa21c0cc7959bc42957efb718a8b5bf4a"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl HSR OS.app"

  zap trash: "~/Library/Application Support/Yaagl HSR OS"
end
