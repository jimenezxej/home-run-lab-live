#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/github-upload"
rm -rf "$OUT"
mkdir -p "$OUT"
cp "$ROOT/app/index.html" "$OUT/"
cp "$ROOT/app/manifest.webmanifest" "$OUT/"
cp "$ROOT/app/icon.svg" "$OUT/"
cp "$ROOT/app/sw.js" "$OUT/"
cp "$ROOT/app/slate.json" "$OUT/"
cp "$ROOT/app/hr-history.json" "$OUT/"
cp "$ROOT/app/live-events.json" "$OUT/"
cat > "$OUT/README_UPLOAD_TO_GITHUB.txt" <<'TXT'
Upload every file in this folder to the root of your GitHub Pages repo.
Then enable: Settings -> Pages -> Deploy from branch -> main -> /root.
Open the Pages URL on iPhone Safari, then Share -> Add to Home Screen.
TXT
cd "$OUT/.."
zip -qr home-run-lab-github-upload.zip github-upload
echo "Created: $ROOT/home-run-lab-github-upload.zip"
