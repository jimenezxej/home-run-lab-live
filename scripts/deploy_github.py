#!/usr/bin/env python3
import subprocess
from pathlib import Path
import sys
import shutil

ROOT = Path.cwd()

def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    if not (ROOT / ".git").exists():
        print("This folder is not a Git repo yet.")
        print("Run this inside your cloned GitHub repo.")
        sys.exit(1)

    run(["python3", "backend/model/scoring.py"])
    run(["python3", "scripts/build_github_pages.py"])

    for p in (ROOT / "dist").iterdir():
        target = ROOT / p.name
        if p.is_file():
            shutil.copy2(p, target)

    run(["git", "add", "."])
    run(["git", "commit", "-m", "Update Home Run Lab 4.0 app and data"])
    run(["git", "push"])

if __name__ == "__main__":
    main()
