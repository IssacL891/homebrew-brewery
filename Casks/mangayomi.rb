cask "mangayomi" do
  version "0.6.25"
  sha256 "7e0d5af5eda75d23e8d51d1b7e63b4d966d5693ada7de108089dc3963ae56a1d"
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
