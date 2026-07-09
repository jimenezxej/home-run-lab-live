#!/usr/bin/env python3
from pathlib import Path
import json
hist = json.loads(Path("data/hr-history.json").read_text())
print("HR history total:", len(hist.get("home_runs", [])))
for d in hist.get("dates", [])[:30]:
    print(f"{d}: {len((hist.get('byDate') or {}).get(d, []))} HRs")
