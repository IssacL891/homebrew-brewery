cask "mangayomi" do
  version "0.6.95"
  sha256 "5f79ec3262d76d2bb77eb44cbb2b2113d3f2bb18306a01686371006f40093cc0"

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
