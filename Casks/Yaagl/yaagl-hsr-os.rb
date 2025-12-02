cask "yaagl-hsr-os" do
  version "0.3.3"
  sha256 "07ba7c35a69a03ac658787a807aa684d44862fcf5cff711c2079b55bc12211af"

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
