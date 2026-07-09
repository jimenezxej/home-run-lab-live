#!/usr/bin/env python3
"""Home Run Lab 3.1 — live MLB home run tracker.

Polls the MLB Stats API and writes:
  app/hr-history.json   cumulative HR log
  app/live-events.json  today's in-game HR feed

This is intentionally separate from slate generation so the tracker can update
while the heavier Statcast/FanGraphs pipeline runs less often.
"""
from __future__ import annotations

import argparse
import json
import signal
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
HISTORY_PATH = APP / "hr-history.json"
LIVE_PATH = APP / "live-events.json"
LOG_PATH = ROOT / "hr-tracker.log"
BASE = "https://statsapi.mlb.com/api/v1"
FEED_BASE = "https://statsapi.mlb.com/api/v1.1"
UA = {"User-Agent": "HomeRunLab/3.1 personal research"}
STOP = False


def log(msg: str) -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"Could not read {path.name}: {exc}")
    return default


def get_json(url: str, params: dict[str, Any] | None = None, timeout: int = 25) -> Any:
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(url, params=params or {}, timeout=timeout, headers=UA)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last_exc = exc
            time.sleep(1.0 + attempt)
    raise RuntimeError(f"GET failed {url}: {last_exc}")


def schedule_for(day: str) -> list[dict[str, Any]]:
    data = get_json(f"{BASE}/schedule", {"sportId": 1, "date": day})
    games: list[dict[str, Any]] = []
    for d in data.get("dates", []):
        games.extend(d.get("games", []))
    return games


def feed_for(game_pk: int) -> dict[str, Any]:
    # Correct endpoint is /api/v1.1/game/{gamePk}/feed/live
    return get_json(f"{FEED_BASE}/game/{game_pk}/feed/live")


def team_abbr_from_meta(game: dict[str, Any], side: str) -> str:
    team = game.get("teams", {}).get(side, {}).get("team", {})
    return team.get("abbreviation") or team.get("teamName") or team.get("name") or ""


def last_pitch(play: dict[str, Any]) -> dict[str, Any]:
    for ev in reversed(play.get("playEvents", []) or []):
        details = ev.get("details", {}) or {}
        if details.get("type") or ev.get("pitchData"):
            return ev
    return {}


def parse_home_runs(feed: dict[str, Any], game_meta: dict[str, Any], day: str) -> list[dict[str, Any]]:
    game_pk = int(feed.get("gamePk") or game_meta.get("gamePk"))
    game_data = feed.get("gameData", {})
    venue = (game_data.get("venue") or {}).get("name")
    away = (game_data.get("teams", {}).get("away") or {}).get("abbreviation") or team_abbr_from_meta(game_meta, "away")
    home = (game_data.get("teams", {}).get("home") or {}).get("abbreviation") or team_abbr_from_meta(game_meta, "home")
    status = (game_data.get("status") or {}).get("detailedState") or (game_meta.get("status") or {}).get("detailedState")
    plays = ((feed.get("liveData") or {}).get("plays") or {}).get("allPlays", [])
    out: list[dict[str, Any]] = []
    for play in plays:
        result = play.get("result", {}) or {}
        event_type = (result.get("eventType") or "").lower()
        event_name = (result.get("event") or "").lower()
        if event_type != "home_run" and event_name != "home run":
            continue
        matchup = play.get("matchup", {}) or {}
        about = play.get("about", {}) or {}
        hit = play.get("hitData", {}) or {}
        count = play.get("count", {}) or {}
        batter = matchup.get("batter", {}) or {}
        pitcher = matchup.get("pitcher", {}) or {}
        pitch_ev = last_pitch(play)
        pitch_details = pitch_ev.get("details", {}) or {}
        pitch_type = (pitch_details.get("type") or {}).get("description") or pitch_details.get("description")
        half = (about.get("halfInning") or "").lower()
        batting_team = away if half == "top" else home if half == "bottom" else ""
        at_bat_index = about.get("atBatIndex")
        item = {
            "id": f"{game_pk}-{at_bat_index}-{batter.get('id')}",
            "date": day,
            "gamePk": game_pk,
            "game": f"{away} @ {home}",
            "status": status,
            "inning": about.get("inning"),
            "halfInning": about.get("halfInning"),
            "batter": batter.get("fullName"),
            "batterId": batter.get("id"),
            "team": batting_team,
            "pitcher": pitcher.get("fullName"),
            "pitcherId": pitcher.get("id"),
            "description": result.get("description"),
            "rbi": result.get("rbi"),
            "outs": count.get("outs"),
            "balls": count.get("balls"),
            "strikes": count.get("strikes"),
            "pitchType": pitch_type,
            "exitVelocity": hit.get("launchSpeed"),
            "launchAngle": hit.get("launchAngle"),
            "distance": hit.get("totalDistance"),
            "trajectory": hit.get("trajectory"),
            "hardness": hit.get("hardness"),
            "location": hit.get("location"),
            "venue": venue,
            "updatedAt": now_iso(),
        }
        out.append(item)
    return out


def merge_history(existing: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(x.get("id")): x for x in existing if x.get("id")}
    for item in new_items:
        by_id[str(item["id"])] = item
    def sort_key(x: dict[str, Any]):
        return (str(x.get("date", "")), int(x.get("gamePk") or 0), int(x.get("inning") or 0), str(x.get("id", "")))
    return sorted(by_id.values(), key=sort_key, reverse=True)


def run_once(day: str, include_yesterday: bool = False) -> int:
    days = [day]
    if include_yesterday:
        d0 = datetime.strptime(day, "%Y-%m-%d").date()
        days.append((d0 - timedelta(days=1)).isoformat())
    all_today: list[dict[str, Any]] = []
    all_new: list[dict[str, Any]] = []
    for d in days:
        games = schedule_for(d)
        for game in games:
            pk = game.get("gamePk")
            if not pk:
                continue
            try:
                hrs = parse_home_runs(feed_for(int(pk)), game, d)
                all_new.extend(hrs)
                if d == day:
                    all_today.extend(hrs)
            except Exception as exc:
                log(f"Game {pk}: feed unavailable: {exc}")
    existing_obj = load_json(HISTORY_PATH, {"updatedAt": None, "homeRuns": []})
    existing = existing_obj.get("homeRuns", []) if isinstance(existing_obj, dict) else []
    merged = merge_history(existing, all_new)
    atomic_write(HISTORY_PATH, {"updatedAt": now_iso(), "homeRuns": merged})
    atomic_write(LIVE_PATH, {"updatedAt": now_iso(), "date": day, "events": sorted(all_today, key=lambda x: str(x.get("id")), reverse=True)})
    log(f"{day}: found {len(all_today)} HR today; history now {len(merged)} HR")
    return len(all_today)


def handle_stop(signum: int, frame: Any) -> None:
    global STOP
    STOP = True
    log("Stopping live HR tracker...")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="YYYY-MM-DD, default today")
    parser.add_argument("--loop", type=int, default=0, help="poll interval in minutes; 0 runs once")
    parser.add_argument("--include-yesterday", action="store_true", help="also backfill yesterday for streak context")
    args = parser.parse_args()
    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)
    interval = max(1, args.loop) * 60
    while True:
        try:
            run_once(args.date, include_yesterday=args.include_yesterday)
        except Exception as exc:
            log(f"Tracker error: {exc}")
        if not args.loop or STOP:
            break
        time.sleep(interval)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
