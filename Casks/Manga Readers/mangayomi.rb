cask "mangayomi" do
  version "0.9.8"
  sha256 "9e14f49dfe9d9f543f5d9ee765fc90196f4ac5aef43a1d07a812887e16b094a4"

  url "https://github.com/kodjodevf/mangayomi/releases/download/v#{version}/Mangayomi-v#{version}-macos.dmg"
  name "mangayomi"
  desc "Free and open source application for reading manga, novels, and watching anime"
  homepage "https://github.com/kodjodevf/mangayomi"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Mangayomi.app"
end
