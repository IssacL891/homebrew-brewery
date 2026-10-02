cask "yaagl-zzz-os" do
  version "0.3.20"
  sha256 "0c129adbe7b199ef4105afd80402810b87125d004dd2f15aade45e233274ae68"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Yaagl ZZZ OS.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ OS"
end
