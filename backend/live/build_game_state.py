#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt, urllib.request

ROOT = Path.cwd()
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=probablePitcher,lineups,team"

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def load(path, fallback):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: return fallback
    return fallback

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def status_for(game):
    s = game.get("status") or {}
    coded, abstract, detailed = s.get("codedGameState"), s.get("abstractGameState"), s.get("detailedState") or ""
    live = abstract == "Live" or coded in {"I", "M", "N"}
    final = abstract == "Final" or coded == "F"
    delayed = "Delayed" in detailed
    postponed = "Postponed" in detailed
    if final: board = "final"
    elif live: board = "live"
    elif delayed: board = "delayed"
    elif postponed: board = "postponed"
    else: board = "pregame"
    return {"abstract": abstract, "coded": coded, "detailed": detailed, "boardStatus": board, "lockedForBoard": board in {"live","final","delayed","postponed"}}

def abbr(obj):
    return ((obj or {}).get("team") or {}).get("abbreviation") or (obj or {}).get("abbreviation")

def main():
    slate = load(DATA/"slate.json", None) or load(ROOT/"app"/"slate.json", {})
    slate_date = slate.get("date") or dt.date.today().isoformat()
    try:
        sched = fetch_json(SCHEDULE_URL.format(date=slate_date))
        errors = []
    except Exception as e:
        sched, errors = {"dates":[]}, [str(e)]
    games, team_state, locked, active = [], {}, [], []
    for d in sched.get("dates", []):
        for g in d.get("games", []):
            teams = g.get("teams", {}) or {}
            away, home = abbr(teams.get("away")), abbr(teams.get("home"))
            st = status_for(g)
            games.append({"gamePk":g.get("gamePk"),"gameDate":g.get("gameDate"),"away":away,"home":home,"status":st,"venue":((g.get("venue") or {}).get("name"))})
            for t in [away, home]:
                if not t: continue
                team_state[t] = {"gamePk":g.get("gamePk"),"opponent":home if t==away else away,"boardStatus":st["boardStatus"],"lockedForBoard":st["lockedForBoard"],"gameDate":g.get("gameDate")}
                (locked if st["lockedForBoard"] else active).append(t)
    out = {"version":"8.3","updatedAt":dt.datetime.now().isoformat(),"slateDate":slate_date,"games":games,"teamState":team_state,"lockedTeams":sorted(set(locked)),"activeTeams":sorted(set(active)),"errors":errors}
    save(DATA/"game-state.json", out)
    print(f"Game state: {len(games)} games, {len(out['activeTeams'])} active teams, {len(out['lockedTeams'])} locked teams")

if __name__ == "__main__":
    main()
