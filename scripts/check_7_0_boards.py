#!/usr/bin/env python3
from pathlib import Path
import json

path = Path("data/intelligence.json")
if not path.exists():
    raise SystemExit("Missing data/intelligence.json. Run python3 backend/model/intelligence_engine.py first.")

data = json.loads(path.read_text())
paper = data.get("paperBoard", [])[:15]
longs = data.get("longshotBoard", [])[:15]

print("HOME RUN LAB - best spots on paper")
for x in paper:
    print(f"{x['rank']:>2}. {x['name']:<22} {x['team']:<4} score={x['score']} PA={x['pa']} HR={x['hr']} reasons={', '.join(x['reasons'])}")

print("\nLONGSHOT LAB - overlooked upside")
for x in longs:
    print(f"{x['rank']:>2}. {x['name']:<22} {x['team']:<4} score={x['score']} paperRank={x['paperRank']} PA={x['pa']} HR={x['hr']} order={x['order']} reasons={', '.join(x['reasons'])}")

paper_names = {f"{x['name']}|{x['team']}" for x in paper[:12]}
long_names = {f"{x['name']}|{x['team']}" for x in longs[:12]}
overlap = paper_names & long_names
print(f"\nTop-12 overlap: {len(overlap)}")
if overlap:
    print("Overlap:", sorted(overlap))
else:
    print("Good: boards are not mirroring.")
