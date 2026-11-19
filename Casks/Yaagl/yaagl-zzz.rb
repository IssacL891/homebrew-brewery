cask "yaagl-zzz" do
  version "0.4.1-alpha"
  sha256 "7307d2feb39d8b538ab61aeab7e956412e7e96a96249fb4a1b8158fa5911e08b"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Yaagl ZZZ.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ"
end
