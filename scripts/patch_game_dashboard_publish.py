#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/build_github_pages.py")
if not path.exists():
    raise SystemExit("Missing scripts/build_github_pages.py")

text = path.read_text(encoding="utf-8")

if "game-dashboard.json" not in text:
    anchors = [
        '"intelligence.json",',
        "'intelligence.json',",
        '"scores.json",',
        "'scores.json',",
    ]
    for anchor in anchors:
        if anchor in text:
            text = text.replace(anchor, anchor + '\n        "game-dashboard.json",', 1)
            path.write_text(text, encoding="utf-8")
            print("Added game-dashboard.json to build list.")
            break
    else:
        print("Could not patch copy list automatically; fallback copier will still publish it.")
else:
    print("game-dashboard.json already referenced by build script.")
