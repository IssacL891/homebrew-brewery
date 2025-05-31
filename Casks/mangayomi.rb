cask "mangayomi" do
  version "0.6.1"
  sha256 "3e81c5a6e047212e9645d9eb5095687e4b03eed0d369151fa670c9e90813eb72"

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
