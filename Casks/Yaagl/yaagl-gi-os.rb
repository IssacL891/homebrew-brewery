cask "yaagl-gi-os" do
  version "0.3.7"
  sha256 "eeb1c598f8cb85b66f60dc26b3591a9b70e905cabef0f42cb47e36f9f6ce3d28"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :big_sur"

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
