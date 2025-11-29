cask "yaagl-hsr-os" do
  version "0.3.2"
  sha256 "4180fae79ed20cfd26f2442f0b1f9193b85a2359a2a297779f5cfc41cb747c70"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :big_sur"

  app "Yaagl HSR OS.app"

  zap trash: "~/Library/Application Support/Yaagl HSR OS"
end
