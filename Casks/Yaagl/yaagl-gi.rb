cask "yaagl-gi" do
  version "0.3.15"
  sha256 "4f050f14619552917453819410042b0bad5a4e0da7da99b4235ef0bbc6d6b88f"

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
