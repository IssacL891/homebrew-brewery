cask "anymex" do
  version "3.1.8"
  sha256 "326ec2b45144002dfc8509ef3dc14022a4ee9d6bde4b70271bc984bdd6eb08e2"

  url "https://github.com/RyanYuuki/AnymeX/releases/download/v#{version}/AnymeX.dmg"
  name "AnymeX"
  desc "Multiservice tracking client for anime and managa progress"
  homepage "https://github.com/RyanYuuki/AnymeX"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on :macos

  app "AnymeX.app"
end
