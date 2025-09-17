cask "anymex" do
  version "3.0.1"
  sha256 "8b1199721996f58b38cf65b34332f91029d587e83b449ab298e545530ec97250"

  url "https://github.com/RyanYuuki/AnymeX/releases/download/v#{version}/AnymeX.dmg"
  name "AnymeX"
  desc "AnymeX is a multiservice tracking client designed exclusively for managing and tracking anime and manga progress across AniList, MyAnimeList, and Simkl."
  homepage "https://github.com/RyanYuuki/AnymeX"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "AnymeX.app"
end
