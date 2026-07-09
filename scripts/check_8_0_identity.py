#!/usr/bin/env python3
from pathlib import Path
import json
for fname in ["identity-audit.json","season-stats-audit.json","hitter-season-map.json"]:
    p = Path("data")/fname
    if not p.exists():
        print(f"MISSING {fname}")
        continue
    data = json.loads(p.read_text())
    print(f"\n{fname}")
    for k in ["identityReady","sampleStatsReady","totalHitters","mappedHittersPAgt0","missingSeasonStats","zeroPAHitters","suspiciousCount","unresolvedCount","suspiciousIdentityStats","mappedCount","missingCount"]:
        if k in data:
            print(f"{k}: {data[k]}")
    if data.get("suspicious"):
        print("Suspicious preview:")
        for x in data["suspicious"][:10]:
            print(" ", x)
    if data.get("missing"):
        print("Missing preview:")
        for x in data["missing"][:10]:
            print(" ", x)
print("\nIf identityReady and sampleStatsReady are true, rerun scoring + 7.0 intelligence, then GitHub is the next phase.")
