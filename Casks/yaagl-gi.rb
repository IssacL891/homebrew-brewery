cask "yaagl-gi" do
  version "0.2.27"
  sha256 "ce87b6c2187c5f8007369c065e59e13ecbf6a121f0c37ecce736f422cfa87bf8"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl.app"

  zap trash: "~/Library/Application Support/Yaagl"
end
