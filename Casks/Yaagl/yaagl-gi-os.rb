cask "yaagl-gi-os" do
  version "0.2.29"
  sha256 "306d2384dde85109a7e9565e87bbc8c6070b089f5569a3664a74e039210e03b5"

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
