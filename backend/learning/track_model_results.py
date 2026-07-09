#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt

ROOT = Path.cwd()
DATA = ROOT / "data"

def load(path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback

def norm_name(s):
    return (s or "").lower().replace(".", "").replace(",", "").strip()

def main():
    scores = load(DATA / "scores.json", {"players": []})
    history = load(DATA / "hr-history.json", {"home_runs": []})
    slate = load(DATA / "slate.json", {})
    slate_date = slate.get("date") or dt.date.today().isoformat()
    players = scores.get("players", [])
    today_hrs = [h for h in history.get("home_runs", []) if h.get("date") == slate_date]
    hr_names = {norm_name(h.get("batter")) for h in today_hrs}

    def hits(rows):
        return [p for p in rows if norm_name(p.get("name")) in hr_names]

    result = {
        "version": "4.5",
        "updatedAt": dt.datetime.now().isoformat(),
        "date": slate_date,
        "homeRunsTrackedToday": len(today_hrs),
        "top10": {"count": len(players[:10]), "hits": len(hits(players[:10])), "hitters": [p.get("name") for p in hits(players[:10])]},
        "top12": {"count": len(players[:12]), "hits": len(hits(players[:12])), "hitters": [p.get("name") for p in hits(players[:12])]},
        "top20": {"count": len(players[:20]), "hits": len(hits(players[:20])), "hitters": [p.get("name") for p in hits(players[:20])]},
        "todayHomeRunHitters": [h.get("batter") for h in today_hrs],
        "notes": [
            "This starts model accountability.",
            "Track 14-30 days before tuning weights aggressively.",
            "Top 10-12 goal should be evaluated by actual hit rate over time, not one slate."
        ]
    }
    (DATA / "model-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Model results: top10 {result['top10']['hits']}/{result['top10']['count']}, top12 {result['top12']['hits']}/{result['top12']['count']}")

if __name__ == "__main__":
    main()
