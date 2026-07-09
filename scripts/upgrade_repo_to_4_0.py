#!/usr/bin/env python3
from pathlib import Path
import shutil

ROOT = Path.cwd()
FRONTEND_PUBLIC = ROOT / "frontend" / "public"
FRONTEND_SRC = ROOT / "frontend" / "src"
DATA = ROOT / "data"
BACKEND = ROOT / "backend"

def copy_if_exists(src, dst):
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"copied {src} -> {dst}")

def main():
    print("Home Run Lab 4.0 repo upgrade")
    for p in [FRONTEND_PUBLIC, FRONTEND_SRC, DATA, BACKEND, ROOT / "scripts", ROOT / "tests"]:
        p.mkdir(parents=True, exist_ok=True)

    for name in ["slate.json", "hr-history.json", "live-events.json"]:
        copy_if_exists(ROOT / name, DATA / name)
        copy_if_exists(ROOT / "app" / name, DATA / name)

    for name in ["manifest.webmanifest", "sw.js", "icon.svg"]:
        copy_if_exists(ROOT / name, FRONTEND_PUBLIC / name)
        copy_if_exists(ROOT / "app" / name, FRONTEND_PUBLIC / name)

    if (ROOT / "index.html").exists() and not (ROOT / "legacy-index.backup.html").exists():
        shutil.copy2(ROOT / "index.html", ROOT / "legacy-index.backup.html")
        print("backed up old index.html -> legacy-index.backup.html")

    print("Upgrade structure created.")
    print("Next: python3 backend/model/scoring.py")
    print("Then: python3 scripts/build_github_pages.py")

if __name__ == "__main__":
    main()
