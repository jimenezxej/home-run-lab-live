#!/usr/bin/env python3
"""Build a clean GitHub Pages upload folder from the local Home Run Lab app."""
from __future__ import annotations
import json, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
OUT = ROOT / "github-upload"
REQUIRED = ["index.html", "slate.json", "manifest.webmanifest", "sw.js", "hr-history.json", "live-events.json"]
OPTIONAL = ["icon.svg", "app.js", "styles.css"]

def copytree():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    missing = []
    for name in REQUIRED:
        src = APP / name
        if src.exists(): shutil.copy2(src, OUT / name)
        else: missing.append(name)
    for name in OPTIONAL:
        src = APP / name
        if src.exists(): shutil.copy2(src, OUT / name)
    for d in ["icons", "assets"]:
        src = APP / d
        if src.exists(): shutil.copytree(src, OUT / d)
    if missing:
        raise SystemExit("Missing required files in app/: " + ", ".join(missing))
    (OUT / "README_UPLOAD.txt").write_text("Upload the CONTENTS of this folder to your GitHub Pages repository root.\n", encoding="utf-8")

if __name__ == "__main__":
    copytree()
    print(f"Built GitHub upload folder: {OUT}")
