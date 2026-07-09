#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt

ROOT = Path.cwd()
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

def load(path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback

def norm_pitch_name(name):
    if not name:
        return "UNK"
    s = str(name).lower()
    if "4-seam" in s or "four" in s or s in {"ff", "fastball"}:
        return "4-Seam"
    if "sinker" in s or s == "si":
        return "Sinker"
    if "slider" in s or s == "sl":
        return "Slider"
    if "change" in s or s == "ch":
        return "Changeup"
    if "curve" in s or s == "cu":
        return "Curve"
    if "cutter" in s or s == "fc":
        return "Cutter"
    if "split" in s or s == "fs":
        return "Splitter"
    return str(name).title()

def mix_from_existing(p):
    mix = p.get("mix") or []
    out = []
    if isinstance(mix, list):
        for m in mix:
            if isinstance(m, dict):
                pitch = norm_pitch_name(m.get("pitch") or m.get("type") or m.get("name"))
                pct = m.get("pct") or m.get("percent") or m.get("usage")
                try:
                    pct = round(float(pct), 1)
                except Exception:
                    pct = None
                if pitch and pct is not None:
                    out.append({"pitch": pitch, "pct": pct})
    return sorted(out, key=lambda x: x["pct"], reverse=True)

def placeholder_mix(p):
    hand = str(p.get("hand") or "").upper()
    base = [
        {"pitch": "4-Seam", "pct": 34},
        {"pitch": "Slider", "pct": 24},
        {"pitch": "Changeup", "pct": 16},
        {"pitch": "Curve", "pct": 14},
        {"pitch": "Sinker", "pct": 12}
    ]
    if hand == "L":
        base[1], base[2] = base[2], base[1]
    return base

def make_zone_grid(mix):
    grid = [0 for _ in range(9)]
    if not mix:
        return grid
    for m in mix:
        pct = float(m.get("pct") or 0)
        pitch = str(m.get("pitch") or "").lower()
        if "4-seam" in pitch:
            cells = [1, 0, 2]
        elif "sinker" in pitch:
            cells = [6, 7, 8]
        elif "slider" in pitch:
            cells = [5, 8, 2]
        elif "change" in pitch:
            cells = [6, 7, 3]
        elif "curve" in pitch:
            cells = [7, 6, 8]
        elif "cutter" in pitch:
            cells = [3, 4, 5]
        else:
            cells = [4, 1, 7]
        for j, cell in enumerate(cells):
            grid[cell] += pct / (j + 2)
    maxv = max(grid) if max(grid) else 1
    return [round(v / maxv * 100) for v in grid]

def profile_for(team, p):
    name = p.get("name") or "TBD"
    if name == "TBD":
        return {
            "team": team,
            "name": "TBD",
            "status": "missing",
            "mix": [],
            "zoneGrid": [0]*9,
            "notes": ["Pitcher is TBD. Zone visual appears once a probable starter is available."]
        }

    mix = mix_from_existing(p)
    status = "verified_mix" if mix else "profile_placeholder"
    if not mix:
        mix = placeholder_mix(p)

    return {
        "team": team,
        "name": name,
        "hand": p.get("hand"),
        "status": status,
        "mix": mix,
        "zoneGrid": make_zone_grid(mix),
        "notes": [
            "Pitch mix is sourced from available pitcher profile fields." if status == "verified_mix" else "Pitch-location data is not available yet. This is a labeled visual placeholder, not verified Statcast location data.",
            "Future upgrade: collect actual Statcast pitch locations by pitcher and pitch type."
        ]
    }

def main():
    pp = load(DATA / "pitcher-profiles.json", {"profiles": {}}).get("profiles", {})
    profiles = {team: profile_for(team, p) for team, p in pp.items()}
    out = {
        "version": "5.1",
        "updatedAt": dt.datetime.now().isoformat(),
        "integrityRule": "Zone visuals declare whether they are verified pitch mix or placeholder profiles.",
        "profiles": profiles
    }
    (DATA / "pitch-zone-profiles.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote data/pitch-zone-profiles.json with {len(profiles)} profiles")

if __name__ == "__main__":
    main()
