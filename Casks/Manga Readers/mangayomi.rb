cask "mangayomi" do
  version "0.6.80"
  sha256 "9897ce0bf4263b557b4cd4b3178b5f7a75dbebf0c52832e4d487be20ed8c7062"

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
