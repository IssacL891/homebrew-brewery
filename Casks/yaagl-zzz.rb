cask "yaagl-zzz" do
  version "0.2.27"
  sha256 "97b13a8770267da6dd403112926471eef07c9fcc31a6ec43d96f60963229972a"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl ZZZ.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ"
end
