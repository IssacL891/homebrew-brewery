cask "mangayomi" do
  version "0.6.90"
  sha256 "cb7eac285202a3ff3c6ad3bec231f31f5f4329a53477becc03be15cc36c5cb89"

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
