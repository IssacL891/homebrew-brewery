cask "mangayomi" do
  version "0.7.55"
  sha256 "adc816ada901dd83c1b822c162b0b3e49902be73a6f83b98c66ff4530efda312"

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
