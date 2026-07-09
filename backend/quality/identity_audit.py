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
    identity = load(DATA/"player-identity-map.json", {})
    slate = load(DATA/"slate.json", {"hitters":[]})
    hitters = slate.get("hitters", []) or []
    suspicious = [h for h in hitters if h.get("identitySuspicious")]
    unresolved = [h for h in hitters if not h.get("identityResolved")]
    untrusted = [h for h in hitters if not h.get("identityTrusted")]
    out = {
        "version":"8.0",
        "updatedAt":dt.datetime.now().isoformat(),
        "totalHitters":len(hitters),
        "identityReady": len(hitters)>0 and len(unresolved)<=10 and len(suspicious)<=8,
        "suspiciousCount":len(suspicious),
        "unresolvedCount":len(unresolved),
        "untrustedCount":len(untrusted),
        "suspicious":[{"name":h.get("name"),"team":h.get("team"),"resolved":h.get("resolvedMlbName"),"playerId":h.get("playerId"),"method":h.get("identityMethod")} for h in suspicious],
        "unresolved":[{"name":h.get("name"),"team":h.get("team"),"method":h.get("seasonStatsMethod")} for h in unresolved],
        "rule":"Do not publish if obvious wrong player identities remain."
    }
    (DATA/"identity-audit.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("identityReady:", out["identityReady"])
    print("suspicious:", out["suspiciousCount"], "unresolved:", out["unresolvedCount"])
if __name__ == "__main__": main()
