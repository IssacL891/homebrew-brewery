cask "yaagl-gi-os" do
  version "0.3.0"
  sha256 "047d94e0232ea81a770ac97878deeb9800677bf581e67e2384e0f9b30b9eb5c2"

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
