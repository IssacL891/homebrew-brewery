set -euo pipefail
test -s "$1"
bundle="Dartotsu.app"
mkdir -p "$bundle/Contents/MacOS"
cat > fixture.c <<'C'
int main(void) { return 0; }
C
clang -arch "$(uname -m)" fixture.c -o "$bundle/Contents/MacOS/fixture"
cat > "$bundle/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict><key>CFBundleExecutable</key><string>fixture</string></dict></plist>
PLIST
zip -q -r "$2" "$bundle"
