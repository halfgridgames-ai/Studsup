#!/usr/bin/env bash
# Build the app copy of the web game into www/ and sync it into the Android project.
# The game at the repo root loads three.js and fonts from CDNs; the app gets local copies
# (web-extra/) so it works offline, plus analytics.js (Firebase), monetize.js (ads + purchases)
# and native-share.js.
# Run from anywhere:  bash android-app/sync-web.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/.."
DEST="$HERE/www"

rm -rf "$DEST"
mkdir -p "$DEST"
for name in comm crowd lib models teams icon-192.png icon-512.png logo.png logo@2x.png privacy.html terms.html; do
  cp -R "$ROOT/$name" "$DEST/"
done
cp -R "$HERE"/web-extra/* "$DEST/"

python3 - "$ROOT/index.html" "$DEST/index.html" <<'PY'
import sys
s = open(sys.argv[1], encoding='utf-8').read()
def swap(old, new):
    global s
    if s.count(old) != 1:
        sys.exit('sync-web: expected exactly one ' + repr(old[:60]))
    s = s.replace(old, new)
swap('<link rel="manifest" href="manifest.webmanifest">\n', '')
swap('<link rel="preconnect" href="https://fonts.googleapis.com">\n', '')
swap('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bungee&family=Barlow+Condensed:wght@500;700&family=Orbitron:wght@500;700;800;900&family=Rajdhani:wght@500;600;700&display=swap">',
     '<link rel="stylesheet" href="fonts/fonts.css">')
swap('<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>',
     '<style>#fsBtn{display:none!important}</style>\n<script src="analytics.js"></script>\n<script src="monetize.js"></script>\n<script src="native-share.js"></script>\n<script src="three.min.js"></script>')
open(sys.argv[2], 'w', encoding='utf-8').write(s)
PY

cd "$HERE"
npx cap sync android
