cask "anymex" do
  version "3.2.0"
  sha256 "828324cc6bac707ffb996bf9e7802c8ce5df5f985b2a701a34ae699ccc153e30"

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
