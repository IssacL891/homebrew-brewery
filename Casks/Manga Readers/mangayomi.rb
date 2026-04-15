cask "mangayomi" do
  version "0.7.50"
  sha256 "4ecf9834b1d7d7c52f195475ecc8712541840dd635eff7d2de87439850c0b244"

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
