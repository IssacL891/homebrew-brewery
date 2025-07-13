cask "mangayomi" do
  version "0.6.3"
  sha256 "99cc7e97ff61453cd9d1c3db5ada8cd7cb195a65faa7bbad0fc8610104972684"

  url "https://github.com/kodjodevf/mangayomi/releases/download/v#{version}/Mangayomi-v#{version}-macos.dmg"
  name "mangayomi"
  desc "Free and open source application for reading manga, novels, and watching anime"
  homepage "https://github.com/kodjodevf/mangayomi"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "Mangayomi.app"
end
