cask "mangayomi" do
  version "0.7.70"
  sha256 "0f6141c784978e9f5c7e4c1c2a66004909038a7b892fc01e1ff26fef58f651a7"

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
