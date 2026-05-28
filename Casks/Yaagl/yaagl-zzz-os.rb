cask "yaagl-zzz-os" do
  version "0.3.15"
  sha256 "bd2b160bc5dde8f276f1600ef67779141381a97bc82ae51a765864d051d8de5f"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.ZZZ.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl ZZZ OS.app"

  zap trash: "~/Library/Application Support/Yaagl ZZZ OS"
end
