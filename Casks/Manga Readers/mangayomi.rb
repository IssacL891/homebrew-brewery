# Generated from packages/casks/mangayomi.yaml. Edit the YAML and regenerate.

cask "mangayomi" do
  version "0.9.97"
  sha256 "f857c872d768d86d61728cbd03bf7df97a6e42a29acede255063227913ee341b"

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
