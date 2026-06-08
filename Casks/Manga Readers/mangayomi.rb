cask "mangayomi" do
  version "0.7.80"
  sha256 "a4c600dfbe37670561da55c1e34c782a158090757e00929c5c2826e1752df445"

  url "https://github.com/kodjodevf/mangayomi/releases/download/v#{version}/Mangayomi-v#{version}-macos.dmg"
  name "mangayomi"
  desc "Free and open source application for reading manga, novels, and watching anime"
  homepage "https://github.com/kodjodevf/mangayomi"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Mangayomi.app"
end
