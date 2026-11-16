cask "mangayomi" do
  version "0.9.96"
  sha256 "d00038a37e7ceb48c5597e0cc480adf116386770c22f362ec676a19ca4104743"

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
