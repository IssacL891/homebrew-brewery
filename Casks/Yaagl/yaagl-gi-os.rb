cask "yaagl-gi-os" do
  version "0.2.28"
  sha256 "a92a1e28a078671cd9e22875eff47bca468c981a44b720a28da85e6b39f0f6bb"

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
