cask "mangayomi" do
  version "0.6.75"
  sha256 "d3eb5b67e7da99070beff4166e94ac38be083c7eeb5a64f75d45c201b9a3aa3b"

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
