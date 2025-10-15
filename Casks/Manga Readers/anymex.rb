cask "anymex" do
  version "3.0.2"
  sha256 "5107d5563545c9bf3dd9566486314b23cd7f71c5563461dc4fd81e7b02c02319"

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
