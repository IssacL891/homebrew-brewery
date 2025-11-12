cask "yaagl-hsr-os" do
  version "0.3.1"
  sha256 "4ffc448060152d6c303686c1c21be0b4f44b2ed17f366f3e20808f47015857df"

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
