#!/usr/bin/env python3
from pathlib import Path
import json,sys
p=Path("data/pitcher-profiles.json")
if not p.exists():raise SystemExit("Missing data/pitcher-profiles.json")
d=json.loads(p.read_text(encoding="utf-8"));profiles=d.get("profiles",{})
req=["hr9","fb","gb","fip","siera"];complete=0
print("VERIFIED PITCHER METRICS AUDIT")
print("Source:",d.get("source"));print("Season:",d.get("season"))
for team,x in profiles.items():
    miss=[k for k in req if x.get(k) is None]
    ok=not miss and all(x.get("provenance",{}).get(k,{}).get("source")=="FanGraphs via pybaseball pitching_stats" for k in req)
    if ok:complete+=1
    print(f"{team:4} {str(x.get('name')):24} {'PASS' if ok else 'REVIEW':6} HR/9={x.get('hr9')} FB%={x.get('fb')} GB%={x.get('gb')} FIP={x.get('fip')} SIERA={x.get('siera')} missing={miss}")
print(f"\nComplete profiles: {complete}/{len(profiles)}")
if not profiles:sys.exit(2)
