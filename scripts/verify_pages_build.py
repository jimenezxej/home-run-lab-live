#!/usr/bin/env python3
from pathlib import Path
import json, sys

DIST = Path("dist")
required = ["index.html","app.js","styles.css","slate.json","scores.json","hr-history.json","live-board.json","game-state.json"]
errors = []

for name in required:
    path = DIST / name
    if not path.exists():
        errors.append(f"missing dist/{name}")
    elif path.stat().st_size == 0:
        errors.append(f"empty dist/{name}")

def read_json(name):
    try:
        return json.loads((DIST / name).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid dist/{name}: {exc}")
        return {}

scores = read_json("scores.json")
slate = read_json("slate.json")
history = read_json("hr-history.json")

if not scores.get("players"):
    errors.append("scores.json contains no players")
if not slate.get("hitters"):
    errors.append("slate.json contains no hitters")

if errors:
    print("PAGES BUILD FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

(DIST / ".nojekyll").write_text("", encoding="utf-8")
print(f"PAGES BUILD PASSED: {len(scores.get('players', []))} players, {len(slate.get('hitters', []))} hitters, {len(history.get('home_runs', []))} HRs")
