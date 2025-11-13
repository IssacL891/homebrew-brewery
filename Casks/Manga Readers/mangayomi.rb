cask "mangayomi" do
  version "0.6.70"
  sha256 "28fbfe88ac228811c76204c4351b6bab1287c9d9227972abed1fb6225a2be3d9"

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
