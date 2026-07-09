#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt
DATA = Path("data")
def load(path, fallback):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: return fallback
    return fallback
def main():
    slate = load(DATA/"slate.json", {"hitters":[]})
    hitters = slate.get("hitters", []) or []
    mapped = []
    missing = []
    zero_pa = []
    suspicious = []
    for h in hitters:
        pa = int(h.get("pa") or 0)
        if h.get("identitySuspicious"):
            suspicious.append({"name":h.get("name"),"team":h.get("team"),"resolved":h.get("resolvedMlbName"),"playerId":h.get("playerId")})
        if not h.get("seasonStatsVerified"):
            missing.append({"name":h.get("name"),"team":h.get("team"),"resolved":h.get("resolvedMlbName"),"reason":h.get("seasonStatsMethod")})
        elif pa <= 0:
            zero_pa.append({"name":h.get("name"),"team":h.get("team"),"resolved":h.get("resolvedMlbName"),"playerId":h.get("playerId")})
        else:
            mapped.append({"name":h.get("name"),"team":h.get("team"),"resolved":h.get("resolvedMlbName"),"pa":pa,"h":h.get("h"),"hr":h.get("hr"),"trusted":h.get("identityTrusted")})
    ready = len(hitters)>0 and len(mapped)/max(1,len(hitters)) >= .85
    out = {"version":"8.0","updatedAt":dt.datetime.now().isoformat(),"totalHitters":len(hitters),"mappedHittersPAgt0":len(mapped),"missingSeasonStats":len(missing),"zeroPAHitters":len(zero_pa),"suspiciousIdentityStats":len(suspicious),"sampleStatsReady":ready,"missing":missing,"zeroPA":zero_pa,"suspicious":suspicious,"mappedPreview":mapped[:100]}
    (DATA/"season-stats-audit.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Season stats audit: {len(mapped)} mapped PA>0, {len(missing)} missing, {len(zero_pa)} zero PA, {len(suspicious)} suspicious")
    print("sampleStatsReady:", ready)
if __name__ == "__main__": main()
