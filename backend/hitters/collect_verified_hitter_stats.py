#!/usr/bin/env python3
"""
Home Run Lab 6.0.1 — League-wide verified hitter season stats

Fixes the PA=0 issue by using the MLB Stats API /stats endpoint
instead of relying on active roster lookup only.

Source:
https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&playerPool=ALL&season=YYYY&limit=5000&hydrate=person,team
"""
from pathlib import Path
import json, datetime as dt, urllib.request, unicodedata

DATA = Path("data")
DATA.mkdir(exist_ok=True)

SEASON = dt.date.today().year
STATS_URL = (
    "https://statsapi.mlb.com/api/v1/stats"
    "?stats=season&group=hitting&playerPool=ALL&season={season}"
    "&limit=5000&hydrate=person,team"
)

TEAM_ALIASES = {
    "CHW": "CWS", "CWS": "CWS",
    "WSN": "WSH", "WSH": "WSH",
    "AZ": "ARI", "ARI": "ARI",
    "SDP": "SD", "SD": "SD",
    "SFG": "SF", "SF": "SF",
    "TBR": "TB", "TB": "TB",
    "KCR": "KC", "KC": "KC",
    "LAA": "LAA", "ANA": "LAA",
    "LAD": "LAD",
    "NYA": "NYY", "NYY": "NYY",
    "NYN": "NYM", "NYM": "NYM",
    "ATH": "ATH", "OAK": "ATH",
}

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))

def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))

def norm_name(name):
    s = strip_accents(name or "").lower()
    for token in [".", ",", "'", "’", "-", " jr", " sr", " ii", " iii", " iv"]:
        s = s.replace(token, " ")
    return " ".join(s.split())

def norm_team(t):
    if not t:
        return None
    t = str(t).upper().strip()
    return TEAM_ALIASES.get(t, t)

def to_int(v):
    try:
        if v in (None, ""):
            return None
        return int(float(str(v).replace(",", "")))
    except Exception:
        return None

def to_float(v):
    try:
        if v in (None, ""):
            return None
        return float(v)
    except Exception:
        return None

def calc_iso(avg, slg):
    if avg is None or slg is None:
        return None
    try:
        return round(float(slg) - float(avg), 3)
    except Exception:
        return None

def main():
    url = STATS_URL.format(season=SEASON)
    print("Pulling league-wide season hitting stats from MLB Stats API...")
    data = fetch_json(url)
    splits = ((data.get("stats") or [{}])[0].get("splits") or [])
    print(f"Returned {len(splits)} hitter stat rows")

    players = {}
    name_index = {}
    team_name_index = {}
    errors = []

    for sp in splits:
        person = sp.get("player") or sp.get("person") or {}
        team = sp.get("team") or {}
        stat = sp.get("stat") or {}

        pid = person.get("id")
        name = person.get("fullName") or person.get("displayName")
        abbr = norm_team(team.get("abbreviation") or team.get("teamCode") or team.get("fileCode"))

        if not pid or not name:
            continue

        avg = to_float(stat.get("avg"))
        slg = to_float(stat.get("slg"))
        pa = to_int(stat.get("plateAppearances"))
        ab = to_int(stat.get("atBats"))
        hits = to_int(stat.get("hits"))
        hr = to_int(stat.get("homeRuns"))

        row = {
            "playerId": pid,
            "name": name,
            "nameKey": norm_name(name),
            "team": abbr,
            "season": SEASON,
            "source": "MLB Stats API league-wide season hitting stats",
            "verified": True,
            "gamesPlayed": to_int(stat.get("gamesPlayed")),
            "pa": pa,
            "ab": ab,
            "h": hits,
            "hr": hr,
            "doubles": to_int(stat.get("doubles")),
            "triples": to_int(stat.get("triples")),
            "bb": to_int(stat.get("baseOnBalls")),
            "so": to_int(stat.get("strikeOuts")),
            "rbi": to_int(stat.get("rbi")),
            "runs": to_int(stat.get("runs")),
            "sb": to_int(stat.get("stolenBases")),
            "avg": avg,
            "obp": to_float(stat.get("obp")),
            "slg": slg,
            "ops": to_float(stat.get("ops")),
            "iso": calc_iso(avg, slg),
            "rawStat": stat
        }

        players[str(pid)] = row
        key = row["nameKey"]
        name_index.setdefault(key, []).append(str(pid))
        if abbr:
            team_name_index.setdefault(f"{abbr}|{key}", []).append(str(pid))

    # Sort indexes by PA descending so the best current-season match wins.
    for idx in [name_index, team_name_index]:
        for key, ids in idx.items():
            ids.sort(key=lambda pid: players.get(pid, {}).get("pa") or 0, reverse=True)

    out = {
        "version": "6.0.1",
        "season": SEASON,
        "updatedAt": dt.datetime.now().isoformat(),
        "source": "MLB Stats API league-wide season hitting stats",
        "players": players,
        "nameIndex": name_index,
        "teamNameIndex": team_name_index,
        "errors": errors
    }
    (DATA / "verified-hitter-season-stats.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    nonzero = len([p for p in players.values() if (p.get("pa") or 0) > 0])
    print(f"Wrote {len(players)} hitters; {nonzero} have PA > 0")

if __name__ == "__main__":
    main()
