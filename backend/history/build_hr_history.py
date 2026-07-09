#!/usr/bin/env python3
from pathlib import Path
import argparse, datetime as dt, json, urllib.request, time

DATA = Path("data")
DATA.mkdir(exist_ok=True)

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"
FEED_URL = "https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=35) as r:
        return json.loads(r.read().decode("utf-8"))

def dates(days):
    today = dt.date.today()
    return [(today - dt.timedelta(days=i)).isoformat() for i in range(days)]

def get_games(date_s):
    try:
        data = fetch_json(SCHEDULE_URL.format(date=date_s))
    except Exception as e:
        return [], [f"schedule_error:{e}"]
    games = []
    for d in data.get("dates", []):
        games.extend(d.get("games", []))
    return games, []

def extract_hrs(feed, fallback_date):
    gd = feed.get("gameData", {}) or {}
    live = feed.get("liveData", {}) or {}
    teams = gd.get("teams", {}) or {}
    away = ((teams.get("away") or {}).get("abbreviation"))
    home = ((teams.get("home") or {}).get("abbreviation"))
    venue = (gd.get("venue") or {}).get("name")
    game_pk = (gd.get("game") or {}).get("pk")
    official_date = ((gd.get("datetime") or {}).get("officialDate")) or fallback_date
    out = []
    for play in (((live.get("plays") or {}).get("allPlays")) or []):
        result = play.get("result", {}) or {}
        if result.get("event") != "Home Run":
            continue
        matchup = play.get("matchup", {}) or {}
        about = play.get("about", {}) or {}
        events = play.get("playEvents", []) or []
        ev = events[-1] if events else {}
        details = ev.get("details", {}) if isinstance(ev, dict) else {}
        pitch_data = ev.get("pitchData", {}) if isinstance(ev, dict) else {}
        hit_data = ev.get("hitData", {}) if isinstance(ev, dict) else {}
        batter = matchup.get("batter", {}) or {}
        pitcher = matchup.get("pitcher", {}) or {}
        half = about.get("halfInning")
        team = away if half == "top" else home if half == "bottom" else None
        out.append({
            "verified": True,
            "source": "MLB Stats API game feed",
            "date": official_date,
            "gamePk": game_pk,
            "venue": venue,
            "away": away,
            "home": home,
            "team": team,
            "batter": batter.get("fullName"),
            "batterId": batter.get("id"),
            "pitcher": pitcher.get("fullName"),
            "pitcherId": pitcher.get("id"),
            "inning": about.get("inning"),
            "halfInning": half,
            "description": result.get("description"),
            "rbi": result.get("rbi"),
            "pitchType": ((details.get("type") or {}).get("description")) or details.get("description"),
            "pitchSpeed": pitch_data.get("startSpeed"),
            "exitVelocity": hit_data.get("launchSpeed"),
            "launchAngle": hit_data.get("launchAngle"),
            "distance": hit_data.get("totalDistance")
        })
    return out

def dedupe(rows):
    seen, out = set(), []
    for h in rows:
        key = (h.get("gamePk"), h.get("batterId"), h.get("pitcherId"), h.get("inning"), h.get("halfInning"), h.get("description"))
        if key not in seen:
            seen.add(key)
            out.append(h)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()
    days = max(1, min(30, args.days))

    ds = dates(days)
    by_date = {d: [] for d in ds}
    status = {}

    for d in ds:
        games, errors = get_games(d)
        row = {"games": len(games), "homeRuns": 0, "errors": errors}
        print(f"{d}: {len(games)} games")
        for g in games:
            pk = g.get("gamePk")
            if not pk:
                continue
            try:
                by_date[d].extend(extract_hrs(fetch_json(FEED_URL.format(game_pk=pk)), d))
                time.sleep(0.02)
            except Exception as e:
                row["errors"].append(f"game_{pk}:{e}")
        by_date[d] = dedupe(by_date[d])
        row["homeRuns"] = len(by_date[d])
        status[d] = row
        print(f"  HR: {row['homeRuns']}")

    all_hrs = []
    for d in ds:
        all_hrs.extend(by_date[d])
    all_hrs.sort(key=lambda x: (x.get("date") or "", x.get("gamePk") or 0, x.get("inning") or 0), reverse=True)

    # IMPORTANT: only write HR files. Never touch slate.json.
    out = {
        "version": "8.3",
        "source": "MLB Stats API game feed",
        "verifiedRule": "Only plays where result.event == Home Run are included.",
        "updatedAt": dt.datetime.now().isoformat(),
        "days": days,
        "dates": ds,
        "byDate": by_date,
        "dateStatus": status,
        "home_runs": all_hrs
    }
    (DATA / "hr-history.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote data/hr-history.json with {len(all_hrs)} verified HRs. slate.json was not touched.")

if __name__ == "__main__":
    main()
