#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt
DATA=Path("data")
def load(p,f):
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: return f
    return f
scores=load(DATA/"scores.json",{"players":[]})
audit=load(DATA/"truth-audit.json",{})
manifest=load(DATA/"metric-manifest.json",{})
out={"version":"5.0","updatedAt":dt.datetime.now().isoformat(),"audit":audit,"metricManifest":manifest,"playerCount":len(scores.get("players",[]))}
(DATA/"data-provenance-summary.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print("Wrote data/data-provenance-summary.json")
