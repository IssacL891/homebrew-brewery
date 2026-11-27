# Generated from packages/casks/Manga Readers/dartotsu.yaml. Edit the YAML and regenerate.

cask "dartotsu" do
  version "1.2.2"
  sha256 "70bb489d4f440918d2823e40260525656b25863baf739cdac1b724d58e0e0311"

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
