#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path.cwd()
required = [
    "frontend/src/index.html",
    "frontend/src/app.js",
    "frontend/src/styles.css",
    "scripts/build_github_pages.py",
    "backend/model/scoring.py",
    "backend/tracker/live_hr_tracker.py",
]
ok = True
for path in required:
    if not (ROOT / path).exists():
        print(f"Missing: {path}")
        ok = False
    else:
        print(f"OK: {path}")

for path in ["data/slate.json", "data/hr-history.json", "data/live-events.json"]:
    p = ROOT / path
    if p.exists():
        try:
            json.loads(p.read_text(encoding="utf-8"))
            print(f"JSON OK: {path}")
        except Exception as e:
            print(f"JSON ERROR: {path}: {e}")
            ok = False
    else:
        print(f"Optional data missing: {path}")

print("CHECK PASSED" if ok else "CHECK FAILED")
sys.exit(0 if ok else 1)
