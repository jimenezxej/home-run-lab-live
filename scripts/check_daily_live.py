#!/usr/bin/env python3
from pathlib import Path
import json
for fname in ["season-stats-audit.json","game-state.json","live-board.json","hr-history-audit.json"]:
    p=Path("data")/fname
    print("\n"+fname)
    if not p.exists():
        print("MISSING")
        continue
    d=json.loads(p.read_text())
    for k in ["sampleStatsReady","mappedHittersPAgt0","missingSeasonStats","zeroPAHitters","activeCount","lockedCount","totalHomeRuns","daysCovered","updatedAt"]:
        if k in d: print(f"{k}: {d[k]}")
