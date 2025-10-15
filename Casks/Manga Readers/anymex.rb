cask "anymex" do
  version "3.0.1"
  sha256 "7b79be1e43a7f8c524efbc1a68f0689be539a1a1c47314bccfbb8f249a6596cc"

  url "https://github.com/RyanYuuki/AnymeX/releases/download/v#{version}/AnymeX.dmg"
  name "AnymeX"
  desc "A multiservice tracking client for anime and managa progress"
  homepage "https://github.com/RyanYuuki/AnymeX"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "AnymeX.app"
end
