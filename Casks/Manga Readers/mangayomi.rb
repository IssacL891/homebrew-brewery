cask "mangayomi" do
  version "0.7.1"
  sha256 "e5a904079db5006efa7f28c41b32d77c9b2b5e934aaf88923252f3e4a7a5a46f"

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
