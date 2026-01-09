cask "mangayomi" do
  version "0.7.0"
  sha256 "2a770f33f9720e68f515667abeb029e159eb45bb6422de62400dbee7a47768f0"

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
