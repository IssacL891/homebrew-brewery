cask "yaagl-hsr" do
  version "0.2.29"
  sha256 "efe5a219f26574dcea1e19fa6419967ef2d96d0a35b85c870dcd0bee9a79b6d6"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.HSR.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :high_sierra"

  app "Yaagl HSR.app"

  zap trash: "~/Library/Application Support/Yaagl HSR"
end
