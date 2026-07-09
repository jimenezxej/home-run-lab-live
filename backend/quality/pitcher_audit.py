#!/usr/bin/env python3
"""
Home Run Lab 4.2 Pitcher Audit

Reads data/slate.json or app/slate.json and writes:
- data/pitcher-audit.json
- data/health.json

Purpose:
- Detect missing pitcher fields
- Identify probable pitcher/team gaps
- Create a readable completeness score
- Avoid silent blank boxes in the frontend
"""
from __future__ import annotations
from pathlib import Path
import json
import datetime as dt
from typing import Any, Dict, List

REQUIRED = [
    "name", "team", "hand", "hr9", "barrelA", "hardHitA", "fb", "gb",
    "xera", "fip", "siera", "veloTrend", "mix"
]

IMPORTANT = ["name", "team", "hand", "hr9", "barrelA", "hardHitA", "fb", "gb"]

def load_json(path: Path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback

def find_slate(root: Path) -> Path | None:
    for p in [root / "data" / "slate.json", root / "app" / "slate.json", root / "slate.json"]:
        if p.exists():
            return p
    return None

def missing_fields(p: Dict[str, Any]) -> List[str]:
    missing = []
    for key in REQUIRED:
        value = p.get(key)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(key)
    return missing

def pitcher_score(p: Dict[str, Any]) -> int:
    miss = missing_fields(p)
    important_missing = [x for x in miss if x in IMPORTANT]
    score = 100
    score -= len(important_missing) * 12
    score -= (len(miss) - len(important_missing)) * 5
    return max(0, min(100, score))

def audit(slate: Dict[str, Any]) -> Dict[str, Any]:
    pitchers = slate.get("pitchers", {}) or {}
    games = slate.get("games", []) or []

    rows = []
    for team, p in pitchers.items():
        if not isinstance(p, dict):
            continue
        miss = missing_fields(p)
        rows.append({
            "team": team,
            "name": p.get("name") or "TBD",
            "hand": p.get("hand"),
            "completeness": pitcher_score(p),
            "missing": miss,
            "importantMissing": [x for x in miss if x in IMPORTANT],
            "status": "ok" if pitcher_score(p) >= 80 else "needs_review" if pitcher_score(p) >= 55 else "incomplete",
        })

    missing_probables = []
    teams_seen = set()
    for g in games:
        for side in ["away", "home"]:
            t = g.get(side)
            if t:
                teams_seen.add(t)
                p = pitchers.get(t)
                if not p or not p.get("name") or p.get("name") == "TBD":
                    missing_probables.append(t)

    rows.sort(key=lambda x: x["completeness"])
    avg = round(sum(r["completeness"] for r in rows) / max(1, len(rows)))
    return {
        "version": "4.2",
        "updatedAt": dt.datetime.now().isoformat(),
        "pitcherCount": len(rows),
        "averageCompleteness": avg,
        "incompleteCount": len([r for r in rows if r["status"] != "ok"]),
        "missingProbablePitchers": sorted(set(missing_probables)),
        "pitchers": rows,
    }

def main():
    root = Path.cwd()
    slate_path = find_slate(root)
    if not slate_path:
        raise SystemExit("No slate.json found in data/, app/, or repo root.")

    slate = load_json(slate_path, {})
    result = audit(slate)

    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "pitcher-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    health_path = data_dir / "health.json"
    health = load_json(health_path, {})
    health.update({
        "version": "4.2",
        "updatedAt": dt.datetime.now().isoformat(),
        "slatePath": str(slate_path),
        "pitcherCompleteness": result["averageCompleteness"],
        "incompletePitchers": result["incompleteCount"],
        "missingProbablePitchers": result["missingProbablePitchers"],
    })
    health_path.write_text(json.dumps(health, indent=2), encoding="utf-8")

    print(f"Pitcher audit complete: {result['averageCompleteness']}% avg completeness, {result['incompleteCount']} need review")
    if result["missingProbablePitchers"]:
        print("Missing probable pitchers:", ", ".join(result["missingProbablePitchers"]))

if __name__ == "__main__":
    main()
