cask "yaagl-zzz-os" do
  version "0.3.17"
  sha256 "bc631dc6e2d8cb8e0cdedfd984d3966e86ea926cf15733c41b1cd054be216ecb"

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
