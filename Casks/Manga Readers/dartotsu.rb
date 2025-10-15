cask "dartotsu" do
  version "0.0.3"
  sha256 "60e438d5b516836d37dd62a4fef1b7d2569d244dbe58ce222472d0da8c639205"
  url "https://github.com/aayush2622/Dartotsu/releases/download/v#{version}/Dartotsu-macos-v#{version}.dmg"
  name "Dartotsu"
  desc "A complete rewrite of Dantotsu in Flutter"
  homepage "https://github.com/aayush2622/Dartotsu"

  livecheck do
    url :url
    strategy :git
  end

  app "Dartotsu.app"
end
