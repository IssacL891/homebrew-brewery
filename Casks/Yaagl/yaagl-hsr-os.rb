cask "yaagl-hsr-os" do
  version "0.3.15"
  sha256 "35e220393e5fb8c9705d46fac2d9641152ef1039f37f1774d3ea55a27f87fa6d"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl HSR OS.app"

  zap trash: "~/Library/Application Support/Yaagl HSR OS"
end
