cask "yaagl-zzz-os" do
  version "0.2.28"
  sha256 "0e1190a100efcb49de9954113bb14574e875fb6491ae52498aece6a3a1cd917b"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl ZZZ OS.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ OS"
end
