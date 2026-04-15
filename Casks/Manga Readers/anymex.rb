cask "anymex" do
  version "3.0.6"
  sha256 "a87b86952767eede0a32c2688e1ad788f65d2fc763db9cc03b666959848c82f0"

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
