cask "yaagl-gi" do
  version "0.3.17"
  sha256 "22959bef1fa9382905abf5905bd7ff0061ffbcc31e27c965d1b28ee98d244233"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
