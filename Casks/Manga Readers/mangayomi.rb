cask "mangayomi" do
  version "0.7.60"
  sha256 "094bcf91251ae5c6441f9f12259ae79c486c7988b12aba6ab367662c36c82145"

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
