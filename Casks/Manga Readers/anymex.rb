# Generated from packages/casks/Manga Readers/anymex.yaml. Edit the YAML and regenerate.

cask "anymex" do
  version "3.2.1"
  sha256 "cc1e722cac6fdd66142343aaa10fe26e0d08349e02362825dc03b75cd90515bf"

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
