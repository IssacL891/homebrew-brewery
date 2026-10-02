cask "goofcord" do
  version "2.3.1"
  sha256 "4f333711ff5e836bea2fd944e455a25e66b8abcb6df74c73b7de5177e71f57dd"

  url "https://github.com/Milkshiift/GoofCord/releases/download/v#{version}/GoofCord-#{version}-mac-arm64.dmg"
  name "Goofcord"
  desc "Modified version of Discord with privacy enhancements"
  homepage "https://github.com/Milkshiift/GoofCord"

  livecheck do
    url :url
    strategy :git
  end

  depends_on :macos

  app "Goofcord.app"

  zap trash: "~/Library/Application Support/Goofcord"
end
