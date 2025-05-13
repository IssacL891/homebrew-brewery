cask "mangayomi" do
  version "0.6.0"
  sha256 "78ef5888feaa38297431102adc740fd247afccf4dbc7f6f3d963ce003100ca9e"

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
