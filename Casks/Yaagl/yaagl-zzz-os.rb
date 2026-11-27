# Generated from packages/casks/yaagl-zzz-os.yaml. Edit the YAML and regenerate.

cask "yaagl-zzz-os" do
  version "0.4.0"
  sha256 "6afff5e5cc2ade249e75b4d8c911f4ab700418f1c3b04e6418e8171ee43ff5c3"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  conflicts_with cask: "yaagl-zzz-os-pre"

  depends_on :macos

  app "Yaagl ZZZ OS.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ OS"
end
