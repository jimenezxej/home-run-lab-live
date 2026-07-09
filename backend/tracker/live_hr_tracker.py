#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import datetime as dt
import urllib.request
from typing import Any, Dict, List

MLB_SCHEDULE = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=team,linescore"
MLB_FEED = "https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"

def fetch_json(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def today() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")

def get_game_pks(date: str) -> List[int]:
    data = fetch_json(MLB_SCHEDULE.format(date=date))
    return [g["gamePk"] for d in data.get("dates", []) for g in d.get("games", []) if g.get("gamePk")]

def extract_home_runs_from_feed(feed: Dict[str, Any]) -> List[Dict[str, Any]]:
    game_data = feed.get("gameData", {})
    plays = feed.get("liveData", {}).get("plays", {}).get("allPlays", [])
    game_pk = game_data.get("game", {}).get("pk")
    venue = game_data.get("venue", {}).get("name")
    game_date = game_data.get("datetime", {}).get("officialDate")
    hrs = []

    for play in plays:
        if play.get("result", {}).get("event") != "Home Run":
            continue
        matchup = play.get("matchup", {})
        batter = matchup.get("batter", {})
        pitcher = matchup.get("pitcher", {})
        about = play.get("about", {})
        events = play.get("playEvents", [])
        details = events[-1] if events else {}
        hit_data = details.get("hitData", {}) if isinstance(details, dict) else {}
        pitch_data = details.get("pitchData", {}) if isinstance(details, dict) else {}
        pitch_details = details.get("details", {}) if isinstance(details, dict) else {}

        hrs.append({
            "gamePk": game_pk,
            "date": game_date,
            "venue": venue,
            "inning": about.get("inning"),
            "halfInning": about.get("halfInning"),
            "batter": batter.get("fullName"),
            "batterId": batter.get("id"),
            "pitcher": pitcher.get("fullName"),
            "pitcherId": pitcher.get("id"),
            "description": play.get("result", {}).get("description"),
            "rbi": play.get("result", {}).get("rbi"),
            "exitVelocity": hit_data.get("launchSpeed"),
            "launchAngle": hit_data.get("launchAngle"),
            "distance": hit_data.get("totalDistance"),
            "pitchType": pitch_details.get("type", {}).get("description"),
            "pitchSpeed": pitch_data.get("startSpeed"),
        })
    return hrs

def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for x in items:
        key = (x.get("gamePk"), x.get("batterId"), x.get("pitcherId"), x.get("inning"), x.get("description"))
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out

def main():
    root = Path.cwd()
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    date = today()
    hrs, events = [], []

    for pk in get_game_pks(date):
        try:
            feed = fetch_json(MLB_FEED.format(game_pk=pk))
            game_hrs = extract_home_runs_from_feed(feed)
            hrs.extend(game_hrs)
            events.extend([{"type": "home_run", **hr} for hr in game_hrs])
        except Exception as e:
            events.append({"type": "tracker_error", "gamePk": pk, "error": str(e)})

    history_path = data_dir / "hr-history.json"
    existing = {"home_runs": []}
    if history_path.exists():
        try:
            existing = json.loads(history_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    all_hrs = dedupe(existing.get("home_runs", []) + hrs)
    history_path.write_text(json.dumps({"version": "4.0", "updatedAt": dt.datetime.now().isoformat(), "home_runs": all_hrs}, indent=2), encoding="utf-8")
    (data_dir / "live-events.json").write_text(json.dumps({"version": "4.0", "updatedAt": dt.datetime.now().isoformat(), "events": events}, indent=2), encoding="utf-8")
    print(f"Tracked {len(hrs)} HRs today; history total {len(all_hrs)}")

if __name__ == "__main__":
    main()
