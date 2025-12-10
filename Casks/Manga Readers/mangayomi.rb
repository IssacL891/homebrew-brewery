cask "mangayomi" do
  version "0.6.85"
  sha256 "36dbf543c3d63a9dd4326764fe5e2f0f6ac93e3df1c697c25a3494aef2f5d737"

  url "https://github.com/kodjodevf/mangayomi/releases/download/v#{version}/Mangayomi-v#{version}-macos.dmg"
  name "mangayomi"
  desc "Free and open source application for reading manga, novels, and watching anime"
  homepage "https://github.com/kodjodevf/mangayomi"

  livecheck do
    url :url
    strategy :git
  end

  app "Mangayomi.app"
end
