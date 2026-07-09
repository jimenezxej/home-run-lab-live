#!/usr/bin/env python3
from pathlib import Path
import json, sys
DATA=Path("data")
slate_path=DATA/"slate.json"
if not slate_path.exists():
    print("FAIL: data/slate.json missing")
    sys.exit(1)
slate=json.loads(slate_path.read_text())
hitters=slate.get("hitters",[])
nonzero=[h for h in hitters if int(h.get("pa") or 0)>0]
verified=[h for h in hitters if h.get("seasonStatsVerified")]
ratio=len(nonzero)/max(1,len(hitters))
print(f"Season stat guard: {len(nonzero)}/{len(hitters)} hitters have PA > 0")
if hitters and ratio < 0.85:
    print("FAIL: Too many hitters have PA=0. Re-run identity/stat attachment before building.")
    sys.exit(2)
print("PASS: Season stats protected.")
