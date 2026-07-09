#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt

DATA = Path("data")
FIELDS = ["name","hand","hr9","barrelA","hardHitA","fb","gb","xera","fip","siera","mix"]

def load(path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback

def main():
    profiles = load(DATA/"pitcher-profiles.json", {"profiles":{}}).get("profiles",{})
    coverage = {f: {"verified":0,"missing":0} for f in FIELDS}
    rows = []
    for team,p in profiles.items():
        prov = p.get("provenance",{})
        for f in FIELDS:
            st = prov.get(f,{}).get("status")
            if st == "verified":
                coverage[f]["verified"] += 1
            else:
                coverage[f]["missing"] += 1
        rows.append({"team":team,"name":p.get("name"),"quality":p.get("dataQuality"),"realFields":p.get("realFields",[]),"missingFields":p.get("missingFields",[])})
    total = sum(v["verified"]+v["missing"] for v in coverage.values())
    verified = sum(v["verified"] for v in coverage.values())
    trust = round(verified/max(1,total)*100)
    out = {"version":"5.0","updatedAt":dt.datetime.now().isoformat(),"trustScore":trust,"fieldCoverage":coverage,"pitchers":rows,"rule":"Missing values must display N/A and lower confidence."}
    (DATA/"truth-audit.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Truth audit complete. Trust score: {trust}%")
    for f,c in coverage.items():
        print(f"{f}: {c['verified']} verified / {c['missing']} missing")

if __name__ == "__main__":
    main()
