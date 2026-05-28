cask "anymex" do
  version "3.0.9"
  sha256 "933c42c4317651941739263e90d3b69bd9b939a0faa894082dacd5d72f6b6735"

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
