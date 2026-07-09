#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt
DATA=Path("data")
def load(p,f):
    if p.exists():
        try: return json.loads(p.read_text())
        except Exception: return f
    return f
hist=load(DATA/"hr-history.json",{"dates":[],"byDate":{},"dateStatus":{},"home_runs":[]})
rows=[]
for d in hist.get("dates",[]):
    rows.append({"date":d,"games":hist.get("dateStatus",{}).get(d,{}).get("games",0),"homeRuns":len(hist.get("byDate",{}).get(d,[])),"errors":hist.get("dateStatus",{}).get(d,{}).get("errors",[])})
out={"version":"8.3","updatedAt":dt.datetime.now().isoformat(),"totalHomeRuns":len(hist.get("home_runs",[])),"daysCovered":len(rows),"dates":rows}
(DATA/"hr-history-audit.json").write_text(json.dumps(out,indent=2))
print(f"HR tracker audit: {out['totalHomeRuns']} HRs across {out['daysCovered']} dates")
for r in rows[:5]: print(r)
