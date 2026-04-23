cask "anymex" do
  version "3.0.7"
  sha256 "e4fb4fc9fb9404f575b2477c59bd07ef3121c7b46ac4d1e942a1392c9739f90e"

  url "https://github.com/RyanYuuki/AnymeX/releases/download/v#{version}/AnymeX.dmg"
  name "AnymeX"
  desc "Multiservice tracking client for anime and managa progress"
  homepage "https://github.com/RyanYuuki/AnymeX"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "AnymeX.app"
end
