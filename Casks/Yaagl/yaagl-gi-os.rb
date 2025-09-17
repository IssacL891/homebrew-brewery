cask "yaagl-gi-os" do
  version "0.2.27"
  sha256 "3f622a32c8608c30cf3757e45c79640fe1dd4ef407b00048e5d5b19b3283d7e9"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
