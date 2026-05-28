cask "yaagl-gi-os" do
  version "0.3.15"
  sha256 "cf407e19cfa383a48f640fe2f9f750026a780964c087ceab19a056cba732115f"

  url "https://github.com/yaagl/yet-another-anime-game-launcher/releases/download/#{version}/Yaagl.OS.app.tar.gz"
  name "Yet Another Anime Game Launcher"
  desc "Launcher for an anime game overseas"
  homepage "https://github.com/yaagl/yet-another-anime-game-launcher"

  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: :big_sur

  app "Yaagl OS.app"

  zap trash: "~/Library/Application Support/Yaagl OS"
end
