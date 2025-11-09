cask "mangayomi" do
  version "0.6.60"
  sha256 "6185d09494f3d556cb07b38b3ac099f3d5e95b80d3cb5cb431d18c4274957cd0"

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
