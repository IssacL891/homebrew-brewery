cask "dartotsu" do
  version "1.0.0"
  sha256 "6da82a5767db52da522d18260b87e887b3516ce9d8a9266c7b7b89f484fb22fa"

  url "https://github.com/aayush2622/Dartotsu/releases/download/v#{version}/Dartotsu-macos-v#{version}.dmg"
  name "Dartotsu"
  desc "Complete rewrite of Dantotsu in Flutter"
  homepage "https://github.com/aayush2622/Dartotsu"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Dartotsu.app"
end
