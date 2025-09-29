cask "mangayomi" do
  version "0.6.5"
  sha256 "e74ba1c62b3f2e15168f9091b3294b4a59293f84736627981db6d7784d76537f"

  url "https://github.com/kodjodevf/mangayomi/releases/download/v#{version}/Mangayomi-v#{version}-macos.dmg"
  name "mangayomi"
  desc "Free and open source application for reading manga, novels, and watching anime"
  homepage "https://github.com/kodjodevf/mangayomi"

  livecheck do
    url :url
    strategy :git
  end

  app "Mangayomi.app"
end
