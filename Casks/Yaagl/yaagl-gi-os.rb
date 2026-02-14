cask "yaagl-gi-os" do
  version "0.3.10"
  sha256 "60c91e9bf160a12f6d0242c2371ee79d4acdb24b32a67786e62d301c76194ba6"

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
