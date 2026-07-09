#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt

ROOT = Path.cwd()
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

SOURCE_KEYS = {
    "name": ["name", "fullName"],
    "hand": ["hand", "throws", "pitchHand"],
    "hr9": ["hr9", "hrPer9", "HR_9"],
    "barrelA": ["barrelA", "barrel_rate_allowed", "barrelAllowed"],
    "hardHitA": ["hardHitA", "hard_hit_allowed", "hardHitAllowed"],
    "fb": ["fb", "fbPct", "flyBallPct"],
    "gb": ["gb", "gbPct", "groundBallPct"],
    "xera": ["xera", "xERA"],
    "fip": ["fip", "FIP"],
    "siera": ["siera", "SIERA"],
    "veloTrend": ["veloTrend", "velocityTrend"],
    "mix": ["mix", "pitchMix"]
}
CRITICAL = ["name","hand","hr9","barrelA","hardHitA","fb","gb"]

def load(path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback

def is_tbd(name):
    return not name or str(name).strip().upper() in {"TBD","TBA","UNKNOWN","—","-"}

def find(obj, keys):
    for k in keys:
        v = obj.get(k)
        if v is not None and v != "" and v != [] and v != {}:
            return v, k
    return None, None

def number(v):
    if v is None or v == "":
        return None
    try:
        return round(float(v), 3)
    except Exception:
        return v

def enrich(team, raw):
    raw = raw or {}
    name, name_src = find(raw, SOURCE_KEYS["name"])
    if is_tbd(name):
        fields = {k: None for k in ["hand","hr9","barrelA","hardHitA","fb","gb","xera","fip","siera","veloTrend"]}
        return {
            "team": team, "name": "TBD", **fields, "mix": [],
            "dataQuality": "tbd",
            "realFields": ["name"] if name else [],
            "missingFields": list(SOURCE_KEYS.keys()),
            "provenance": {k: {"status": "missing", "source": None} for k in SOURCE_KEYS},
            "notes": ["Starter not announced. No pitcher metrics are displayed until a real source field is available."],
            "raw": raw
        }

    profile = {"team": team, "name": name}
    provenance = {"name": {"status": "verified", "source": name_src}}
    real, missing = ["name"], []

    for field in ["hand","hr9","barrelA","hardHitA","fb","gb","xera","fip","siera","veloTrend","mix"]:
        v, src = find(raw, SOURCE_KEYS[field])
        if v is None:
            profile[field] = [] if field == "mix" else None
            provenance[field] = {"status": "missing", "source": None}
            missing.append(field)
        else:
            profile[field] = v if field == "mix" else number(v)
            provenance[field] = {"status": "verified", "source": src}
            real.append(field)

    crit = len([f for f in CRITICAL if f in real])
    quality = "complete" if crit >= 6 else "partial" if crit >= 4 else "limited" if crit >= 2 else "poor"

    notes = []
    if missing:
        notes.append("Missing fields are shown as N/A. No neutral placeholders are used.")
    if "gb" in missing:
        notes.append("GB% is missing from the source, so it is N/A, not a default value.")
    if "fb" in missing:
        notes.append("FB% is missing from the source, so it is N/A.")
    if "fip" in missing or "siera" in missing:
        notes.append("FIP/SIERA are unavailable from the current source.")
    if not profile["mix"]:
        notes.append("Pitch mix is unavailable from the current source.")

    profile.update({"dataQuality": quality, "realFields": real, "missingFields": missing, "provenance": provenance, "notes": notes, "raw": raw})
    return profile

def main():
    slate = load(DATA / "slate.json", None) or load(ROOT / "app" / "slate.json", {})
    profiles = {team: enrich(team, p) for team, p in (slate.get("pitchers", {}) or {}).items()}
    out = {"version":"5.0","updatedAt":dt.datetime.now().isoformat(),"integrityRule":"No fake pitcher values. Missing source fields display N/A.","profiles":profiles}
    (DATA / "pitcher-profiles.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote data/pitcher-profiles.json with {len(profiles)} profiles")

if __name__ == "__main__":
    main()
