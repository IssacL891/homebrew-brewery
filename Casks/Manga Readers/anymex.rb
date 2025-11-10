cask "anymex" do
  version "3.0.3"
  sha256 "882232e5e37eddf2169c924dea5ff33fa9732aba30ee8034f59cfe12a45ce608"

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
