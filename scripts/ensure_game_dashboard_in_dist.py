#!/usr/bin/env python3
from pathlib import Path
import shutil, json

source = Path("data/game-dashboard.json")
if not source.exists():
    raise SystemExit("Missing data/game-dashboard.json. Build it first.")

data = json.loads(source.read_text(encoding="utf-8"))
games = data.get("games", []) if isinstance(data, dict) else []
if not games:
    raise SystemExit("data/game-dashboard.json contains no games.")

dist = Path("dist")
dist.mkdir(exist_ok=True)
target = dist / "game-dashboard.json"
shutil.copy2(source, target)
print(f"Copied {source} to {target} with {len(games)} games.")
