cask "anymex" do
  version "3.0.4"
  sha256 "a722fc4fd2462c46de8eeed180942b4fda92f5c7fcc2433f00622cc2f1bf4810"

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
