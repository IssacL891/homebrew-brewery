cask "goofcord" do
  version "1.11.0"
  sha256 "4b8b7fdd91a44113b0733f6467d5a47f1958b7c671c117e264b0449a619857a2"
  url "https://github.com/Milkshiift/GoofCord/releases/download/v#{version}/GoofCord-#{version}-mac-arm64.dmg"
  name "Goofcord"
  desc "A modified version of Discord with privacy enhancements"
  homepage "https://github.com/Milkshiift/GoofCord"
  livecheck do
    url :url
    strategy :git
  end

  depends_on macos: ">= :big_sur"

  app "Goofcord.app"
  zap trash: "~/Library/Application Support/Goofcord"
end
