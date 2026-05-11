cask "mangayomi" do
  version "0.7.75"
  sha256 "387553d5536b9f5faff1a624fcb8294be240b4ed7df999faffee2fac40add9cd"

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
