cask "yaagl-gi-os" do
  version "0.3.6"
  sha256 "8087daae6ebf9ecffbc73d7375f02772d113c29846f2c3000541bab7d83948d2"

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
