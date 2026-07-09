#!/usr/bin/env python3
from pathlib import Path
import json
scores_path=Path("data/scores.json"); slate_path=Path("data/slate.json")
if scores_path.exists():
    scores=json.loads(scores_path.read_text()); players=scores.get("players",[])
    print("Top 30 PA check from scores.json:")
    for p in players[:30]:
        pr=p.get("profile",{})
        print(f"{str(p.get('name'))[:24]:24} {str(p.get('team')):4} PA={pr.get('sampleSize')} H={pr.get('seasonHits')} HR={pr.get('seasonHR')} tier={p.get('boardTier')} edge={p.get('scores',{}).get('hr_edge')}")
print()
if slate_path.exists():
    slate=json.loads(slate_path.read_text()); hitters=slate.get("hitters",[])
    nonzero=[h for h in hitters if int(h.get("pa") or 0)>0]
    print(f"Slate hitters with PA > 0: {len(nonzero)} / {len(hitters)}")
    for h in hitters[:35]:
        print(f"{str(h.get('name'))[:24]:24} {str(h.get('team')):4} PA={h.get('pa')} H={h.get('h')} HR={h.get('hr')} verified={h.get('seasonStatsVerified')} method={h.get('seasonStatsMethod')} resolved={h.get('resolvedMlbName')}")
