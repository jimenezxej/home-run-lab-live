#!/usr/bin/env python3
from pathlib import Path
import json, shutil

DATA = Path("data")
DATA.mkdir(exist_ok=True)

FILES = [
    "slate.json","scores.json","scorecards.json","intelligence.json",
    "live-board.json","game-state.json","hr-history.json","hr-history-audit.json",
    "pitcher-profiles.json","pitch-zone-profiles.json","player-identity-map.json",
    "identity-audit.json","hitter-season-map.json","season-stats-audit.json",
    "glossary.json","live-events.json","manual-player-overrides.json"
]

def useful(path):
    if not path.exists() or path.stat().st_size < 3:
        return False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return value not in ({}, [], None)

for name in FILES:
    root = Path(name)
    target = DATA / name
    if not useful(target) and useful(root):
        shutil.copy2(root, target)
        print("Seeded", target)
