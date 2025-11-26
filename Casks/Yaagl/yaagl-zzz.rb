cask "yaagl-zzz" do
  version "0.3.2"
  sha256 "4fda6c23b6985e21d5dcf444aab781d03742250e372c08b319d472ee7bbddcab"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :big_sur"

  app "Yaagl ZZZ.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ"
end
