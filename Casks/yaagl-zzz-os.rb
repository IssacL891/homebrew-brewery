cask "yaagl-zzz-os" do
  version "0.2.27"
  sha256 "8fb7c43d397f2385f143f19d551ef6f8600973e40a5808e6569116774857b5cb"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl ZZZ OS.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ OS"
end
