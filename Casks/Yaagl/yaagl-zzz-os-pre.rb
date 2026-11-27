# Generated from packages/casks/yaagl-zzz-os.yaml. Edit the YAML and regenerate.

cask "yaagl-zzz-os-pre" do
  version "0.4.1-alpha"
  sha256 "0274636ab279558aea54790947fbc5b2cfff4a8c21c1d4c75be899b721dbc50c"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  conflicts_with cask: "yaagl-zzz-os"

  depends_on :macos

  app "Yaagl ZZZ OS.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ OS"
end
