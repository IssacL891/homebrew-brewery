cask "mangayomi" do
  version "0.6.2"
  sha256 "e9ee1564fe5c48e9af00223c0a98492c6550d77c35919b64bff1c6bab284e58e"

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
