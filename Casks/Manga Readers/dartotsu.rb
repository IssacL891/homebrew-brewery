cask "dartotsu" do
  version "0.0.4"
  sha256 "67e107210ac5af20c7342b77d3950271a3b95b14c0f6e7037d77ed0a179cb31a"

  url "https://github.com/aayush2622/Dartotsu/releases/download/v#{version}/Dartotsu-macos-v#{version}.dmg"
  name "Dartotsu"
  desc "Complete rewrite of Dantotsu in Flutter"
  homepage "https://github.com/aayush2622/Dartotsu"

  livecheck do
    url :url
    strategy :git
  end

  app "Dartotsu.app"
end
