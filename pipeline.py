#!/usr/bin/env python3
"""
THE HOME RUN LAB — data pipeline
Pulls today's MLB slate (schedule, probable pitchers, confirmed/projected lineups),
Statcast + FanGraphs metrics, bullpen availability, and stadium weather, then writes
app/slate.json for the web app.

Personal-use tool. Data sources:
  - MLB Stats API (statsapi.mlb.com)  : schedule, lineups, rosters, bio, BvP, boxscores
  - Baseball Savant via pybaseball    : pitch-level Statcast, leaderboards
  - FanGraphs via pybaseball          : season stats, Stuff+/Location+, SIERA, etc.
  - Open-Meteo (open-meteo.com)       : hourly stadium weather, no API key

Usage:
  python pipeline.py                  # build today's slate.json
  python pipeline.py --date 2026-07-08
  python pipeline.py --loop 15        # rebuild every 15 minutes (auto-updating lineups)
  python pipeline.py --demo           # write a fake slate.json (no internet needed)
  python pipeline.py --quick          # skip slow extras (BvP lookups)

First run of a real slate is slow (~5-15 min) while the per-player Statcast cache
builds. After that, runs take ~1-3 minutes.

Every external feed is wrapped so a failure degrades to neutral values instead of
crashing; the coverage report at the end tells you what filled and what didn't.
"""

import argparse, json, math, os, sys, time, random, traceback
from datetime import date, datetime, timedelta, timezone

import requests

try:
    import pandas as pd
except ImportError:
    print("pandas is required:  pip install pandas"); sys.exit(1)

# pybaseball is only needed for real runs (not --demo)
try:
    import pybaseball as pyb
    try:
        pyb.cache.enable()
    except Exception:
        pass
    HAVE_PYB = True
except ImportError:
    HAVE_PYB = False

# ----------------------------------------------------------------------------
# Static tables (edit freely)
# ----------------------------------------------------------------------------
UA = {"User-Agent": "HomeRunLab/1.0 (personal research tool)"}
MLB = "https://statsapi.mlb.com/api/v1"

TEAMS = {  # mlbam id -> abbreviation
    108: "LAA", 109: "ARI", 110: "BAL", 111: "BOS", 112: "CHC", 113: "CIN",
    114: "CLE", 115: "COL", 116: "DET", 117: "HOU", 118: "KC",  119: "LAD",
    120: "WSH", 121: "NYM", 133: "ATH", 134: "PIT", 135: "SD",  136: "SEA",
    137: "SF",  138: "STL", 139: "TB",  140: "TEX", 141: "TOR", 142: "MIN",
    143: "PHI", 144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL",
}
ABBR2ID = {v: k for k, v in TEAMS.items()}

FG_TEAM = {  # our abbr -> FanGraphs abbr
    "KC": "KCR", "SD": "SDP", "SF": "SFG", "TB": "TBR", "WSH": "WSN",
    "CWS": "CHW", "ATH": "OAK",
}
def fg_abbr(a): return FG_TEAM.get(a, a)

# Park table. HR factors are approximate multi-year Savant-style factors on a
# 100 = league-average scale — tune them to taste, the engine reads them as-is.
# cf_bearing = compass bearing (deg) from home plate toward center field, approximate.
PARKS = {
    "ARI": dict(name="Chase Field",              lat=33.4453, lon=-112.0667, alt=1086, roof="retractable", cf=0,   hr=103, lf=104, cfF=100, rf=104, fence="330 / 407 / 335", wall="7-25 ft"),
    "ATL": dict(name="Truist Park",              lat=33.8907, lon=-84.4677,  alt=1050, roof="open",        cf=145, hr=105, lf=106, cfF=102, rf=106, fence="335 / 400 / 325", wall="6-16 ft"),
    "BAL": dict(name="Camden Yards",             lat=39.2839, lon=-76.6217,  alt=40,   roof="open",        cf=31,  hr=101, lf=94,  cfF=100, rf=108, fence="337 / 400 / 318", wall="7-13 ft"),
    "BOS": dict(name="Fenway Park",              lat=42.3467, lon=-71.0972,  alt=20,   roof="open",        cf=52,  hr=96,  lf=104, cfF=96,  rf=93,  fence="310 / 390 / 302", wall="37 ft LF"),
    "CHC": dict(name="Wrigley Field",            lat=41.9484, lon=-87.6553,  alt=595,  roof="open",        cf=35,  hr=102, lf=103, cfF=101, rf=103, fence="355 / 400 / 353", wall="11-15 ft"),
    "CWS": dict(name="Rate Field",               lat=41.8299, lon=-87.6338,  alt=595,  roof="open",        cf=127, hr=108, lf=109, cfF=104, rf=110, fence="330 / 400 / 335", wall="8 ft"),
    "CIN": dict(name="Great American Ball Park", lat=39.0975, lon=-84.5066,  alt=490,  roof="open",        cf=120, hr=114, lf=113, cfF=108, rf=118, fence="328 / 404 / 325", wall="8-12 ft"),
    "CLE": dict(name="Progressive Field",        lat=41.4962, lon=-81.6852,  alt=650,  roof="open",        cf=0,   hr=99,  lf=100, cfF=97,  rf=102, fence="325 / 405 / 325", wall="9-19 ft"),
    "COL": dict(name="Coors Field",              lat=39.7559, lon=-104.9942, alt=5200, roof="open",        cf=25,  hr=112, lf=110, cfF=115, rf=111, fence="347 / 415 / 350", wall="8 ft"),
    "DET": dict(name="Comerica Park",            lat=42.3390, lon=-83.0485,  alt=600,  roof="open",        cf=150, hr=95,  lf=97,  cfF=92,  rf=98,  fence="345 / 412 / 330", wall="7-13 ft"),
    "HOU": dict(name="Daikin Park",              lat=29.7573, lon=-95.3555,  alt=45,   roof="retractable", cf=343, hr=107, lf=114, cfF=100, rf=104, fence="315 / 409 / 326", wall="10-25 ft"),
    "KC":  dict(name="Kauffman Stadium",         lat=39.0517, lon=-94.4803,  alt=750,  roof="open",        cf=45,  hr=92,  lf=94,  cfF=90,  rf=94,  fence="330 / 410 / 330", wall="8 ft"),
    "LAA": dict(name="Angel Stadium",            lat=33.8003, lon=-117.8827, alt=160,  roof="open",        cf=46,  hr=101, lf=104, cfF=98,  rf=100, fence="330 / 396 / 330", wall="8-18 ft"),
    "LAD": dict(name="Dodger Stadium",           lat=34.0739, lon=-118.2400, alt=510,  roof="open",        cf=26,  hr=104, lf=105, cfF=100, rf=105, fence="330 / 395 / 330", wall="8 ft"),
    "MIA": dict(name="loanDepot park",           lat=25.7781, lon=-80.2197,  alt=10,   roof="retractable", cf=40,  hr=94,  lf=95,  cfF=92,  rf=96,  fence="344 / 400 / 335", wall="7-11 ft"),
    "MIL": dict(name="American Family Field",    lat=43.0280, lon=-87.9712,  alt=635,  roof="retractable", cf=132, hr=106, lf=107, cfF=103, rf=108, fence="342 / 400 / 337", wall="8 ft"),
    "MIN": dict(name="Target Field",             lat=44.9817, lon=-93.2776,  alt=815,  roof="open",        cf=90,  hr=100, lf=101, cfF=98,  rf=101, fence="339 / 404 / 328", wall="8-23 ft"),
    "NYM": dict(name="Citi Field",               lat=40.7571, lon=-73.8458,  alt=10,   roof="open",        cf=25,  hr=99,  lf=101, cfF=95,  rf=101, fence="335 / 408 / 330", wall="8-12 ft"),
    "NYY": dict(name="Yankee Stadium",           lat=40.8296, lon=-73.9262,  alt=55,   roof="open",        cf=75,  hr=110, lf=102, cfF=100, rf=121, fence="318 / 408 / 314", wall="8 ft"),
    "ATH": dict(name="Sutter Health Park",       lat=38.5802, lon=-121.5133, alt=30,   roof="open",        cf=60,  hr=101, lf=102, cfF=99,  rf=102, fence="330 / 403 / 325", wall="8 ft"),
    "PHI": dict(name="Citizens Bank Park",       lat=39.9061, lon=-75.1665,  alt=30,   roof="open",        cf=9,   hr=108, lf=110, cfF=103, rf=109, fence="329 / 401 / 330", wall="6-13 ft"),
    "PIT": dict(name="PNC Park",                 lat=40.4469, lon=-80.0057,  alt=730,  roof="open",        cf=118, hr=94,  lf=90,  cfF=94,  rf=99,  fence="325 / 399 / 320", wall="6-21 ft"),
    "SD":  dict(name="Petco Park",               lat=32.7076, lon=-117.1570, alt=20,   roof="open",        cf=0,   hr=97,  lf=99,  cfF=94,  rf=98,  fence="336 / 396 / 322", wall="4-11 ft"),
    "SEA": dict(name="T-Mobile Park",            lat=47.5914, lon=-122.3325, alt=20,   roof="retractable", cf=49,  hr=97,  lf=99,  cfF=94,  rf=97,  fence="331 / 401 / 327", wall="8 ft"),
    "SF":  dict(name="Oracle Park",              lat=37.7786, lon=-122.3893, alt=10,   roof="open",        cf=87,  hr=85,  lf=94,  cfF=84,  rf=78,  fence="339 / 391 / 309", wall="25 ft RF"),
    "STL": dict(name="Busch Stadium",            lat=38.6226, lon=-90.1928,  alt=465,  roof="open",        cf=62,  hr=95,  lf=96,  cfF=93,  rf=96,  fence="336 / 400 / 335", wall="8 ft"),
    "TB":  dict(name="George M. Steinbrenner Field", lat=27.9803, lon=-82.5067, alt=10, roof="open",       cf=75,  hr=104, lf=101, cfF=100, rf=112, fence="318 / 408 / 314", wall="8 ft"),
    "TEX": dict(name="Globe Life Field",         lat=32.7473, lon=-97.0847,  alt=550,  roof="retractable", cf=45,  hr=101, lf=103, cfF=98,  rf=102, fence="329 / 407 / 326", wall="8-14 ft"),
    "TOR": dict(name="Rogers Centre",            lat=43.6414, lon=-79.3894,  alt=250,  roof="retractable", cf=0,   hr=106, lf=107, cfF=103, rf=108, fence="328 / 400 / 328", wall="10-16 ft"),
    "WSH": dict(name="Nationals Park",           lat=38.8730, lon=-77.0074,  alt=25,   roof="open",        cf=28,  hr=101, lf=102, cfF=98,  rf=103, fence="336 / 402 / 335", wall="8-14 ft"),
}

PITCH_BUCKETS = {
    "4-Seam Fastball": "4-Seam", "Sinker": "Sinker", "Cutter": "Cutter",
    "Slider": "Slider", "Sweeper": "Slider", "Slurve": "Slider",
    "Changeup": "Changeup", "Split-Finger": "Changeup", "Forkball": "Changeup", "Screwball": "Changeup",
    "Curveball": "Curve", "Knuckle Curve": "Curve", "Eephus": "Curve", "Knuckleball": "Curve",
}
BUCKETS = ["4-Seam", "Sinker", "Slider", "Cutter", "Changeup", "Curve"]

# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def fetch_json(url, params=None, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=25)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(1.2 * (i + 1))
    return None

def nz(v, d=None):
    """None/NaN-safe value."""
    try:
        if v is None: return d
        if isinstance(v, float) and math.isnan(v): return d
        return v
    except Exception:
        return d

def fnum(v, d=None):
    v = nz(v, None)
    if v is None: return d
    try:
        if isinstance(v, str): v = v.replace("%", "").strip()
        return float(v)
    except Exception:
        return d

def rnd(v, n=1):
    v = fnum(v)
    return None if v is None else round(v, n)

def pick_col(df, candidates):
    """Return the first column name that exists in df (case-insensitive)."""
    if df is None: return None
    low = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in low: return low[c.lower()]
    return None

def row_val(row, df, candidates, default=None):
    c = pick_col(df, candidates)
    if c is None or row is None: return default
    return fnum(row.get(c), default)

def ang_diff(a, b):
    d = (a - b + 180) % 360 - 180
    return abs(d)

def xhr_prob(ev, la):
    """Crude P(HR | EV, LA) used for the expected-HR proxy. Tunable."""
    if ev is None or la is None: return 0.0
    if ev < 88 or la < 12 or la > 45: return 0.0
    p_ev = 1.0 / (1.0 + math.exp(-(ev - 100.5) / 2.6))
    p_la = math.exp(-((la - 27.5) ** 2) / (2 * 8.0 ** 2))
    return max(0.0, min(0.95, p_ev * p_la * 1.15))

COVERAGE = {}
def cov(key, ok): COVERAGE[key] = COVERAGE.get(key, [0, 0]); COVERAGE[key][0 if ok else 1] += 1

# ----------------------------------------------------------------------------
# MLB Stats API
# ----------------------------------------------------------------------------
def get_schedule(d):
    j = fetch_json(f"{MLB}/schedule", {
        "sportId": 1, "date": d.isoformat(),
        "hydrate": "probablePitcher,lineups,team,venue",
    })
    games = []
    for day in (j or {}).get("dates", []):
        for g in day.get("games", []):
            if g.get("gameType") not in ("R", "F", "D", "L", "W", "P"):  # regular + postseason
                continue
            home_id = g["teams"]["home"]["team"]["id"]; away_id = g["teams"]["away"]["team"]["id"]
            if home_id not in TEAMS or away_id not in TEAMS: continue
            games.append({
                "gamePk": g["gamePk"],
                "gameDate": g["gameDate"],  # UTC ISO
                "status": g.get("status", {}).get("detailedState", ""),
                "home": TEAMS[home_id], "away": TEAMS[away_id],
                "home_id": home_id, "away_id": away_id,
                "probables": {
                    "home": (g["teams"]["home"].get("probablePitcher") or {}).get("id"),
                    "away": (g["teams"]["away"].get("probablePitcher") or {}).get("id"),
                },
                "lineups": g.get("lineups") or {},
            })
    return games

def people_info(ids):
    """id -> {name, bat, throw}"""
    out = {}
    ids = [i for i in set(ids) if i]
    for i in range(0, len(ids), 90):
        chunk = ids[i:i + 90]
        j = fetch_json(f"{MLB}/people", {"personIds": ",".join(map(str, chunk))})
        for p in (j or {}).get("people", []):
            out[p["id"]] = {
                "name": p.get("boxscoreName") or p.get("lastInitName") or p.get("fullName"),
                "full": p.get("fullName"),
                "bat": (p.get("batSide") or {}).get("code", "R"),
                "throw": (p.get("pitchHand") or {}).get("code", "R"),
            }
    return out

def lineup_from_schedule(game, side):
    lu = game["lineups"].get(f"{side}Players") or []
    return [p["id"] for p in lu][:9]

def last_lineup(team_id, before_date, lookback=6):
    """Most recent completed game's batting order for a team (projection fallback)."""
    start = (before_date - timedelta(days=lookback)).isoformat()
    end = (before_date - timedelta(days=1)).isoformat()
    j = fetch_json(f"{MLB}/schedule", {"sportId": 1, "teamId": team_id,
                                       "startDate": start, "endDate": end})
    pks = []
    for day in (j or {}).get("dates", []):
        for g in day.get("games", []):
            if g.get("status", {}).get("codedGameState") == "F":
                pks.append((g["gameDate"], g["gamePk"], g["teams"]["home"]["team"]["id"] == team_id))
    if not pks: return []
    pks.sort(reverse=True)
    _, pk, is_home = pks[0]
    box = fetch_json(f"{MLB}/game/{pk}/boxscore")
    side = "home" if is_home else "away"
    try:
        order = (box["teams"][side].get("battingOrder") or [])[:9]
        return [int(x) for x in order]
    except Exception:
        return []

def roster_pitchers(team_id):
    j = fetch_json(f"{MLB}/teams/{team_id}/roster", {"rosterType": "active"})
    out = []
    for r in (j or {}).get("roster", []):
        if r.get("position", {}).get("code") == "1":
            out.append(r["person"]["id"])
    return out

def bvp(batter_id, pitcher_id):
    j = fetch_json(f"{MLB}/people/{batter_id}/stats", {
        "stats": "vsPlayer", "group": "hitting", "opposingPlayerId": pitcher_id})
    try:
        for s in j.get("stats", []):
            if s.get("type", {}).get("displayName") in ("vsPlayerTotal", "vsPlayer"):
                for sp in s.get("splits", []):
                    st = sp.get("stat", {})
                    if st.get("plateAppearances"):
                        return {"pa": int(st.get("plateAppearances", 0)),
                                "hr": int(st.get("homeRuns", 0)),
                                "slg": fnum(st.get("slg"), None)}
    except Exception:
        pass
    return {"pa": 0, "hr": 0, "slg": None}

def recent_reliever_pitches(team_id, d, days=3):
    """pitcher_id -> [pitches_day1(yesterday), day2, day3] over the last `days` days."""
    start = (d - timedelta(days=days)).isoformat(); end = (d - timedelta(days=1)).isoformat()
    j = fetch_json(f"{MLB}/schedule", {"sportId": 1, "teamId": team_id,
                                       "startDate": start, "endDate": end})
    usage = {}
    for day in (j or {}).get("dates", []):
        for g in day.get("games", []):
            if g.get("status", {}).get("codedGameState") != "F": continue
            age = (d - date.fromisoformat(day["date"])).days  # 1 = yesterday
            box = fetch_json(f"{MLB}/game/{g['gamePk']}/boxscore")
            if not box: continue
            side = "home" if g["teams"]["home"]["team"]["id"] == team_id else "away"
            for key, pl in box["teams"][side].get("players", {}).items():
                st = (pl.get("stats") or {}).get("pitching") or {}
                n = st.get("numberOfPitches") or st.get("pitchesThrown")
                if n:
                    pid = pl["person"]["id"]
                    usage.setdefault(pid, {})[age] = usage.setdefault(pid, {}).get(age, 0) + int(n)
    return usage

# ----------------------------------------------------------------------------
# Leaderboards (season-level) — all optional
# ----------------------------------------------------------------------------
def load_leaderboards(season):
    lb = {}
    def grab(key, fn, *a, **k):
        try:
            lb[key] = fn(*a, **k); log(f"  ✓ {key}: {len(lb[key])} rows")
        except Exception as e:
            lb[key] = None; log(f"  ✗ {key} unavailable ({type(e).__name__}) — using fallbacks")
    log("Loading season leaderboards…")
    grab("bat_ev",  pyb.statcast_batter_exitvelo_barrels, season, 25)
    grab("bat_x",   pyb.statcast_batter_expected_stats,   season, 25)
    grab("pit_ev",  pyb.statcast_pitcher_exitvelo_barrels, season, 30)
    grab("pit_x",   pyb.statcast_pitcher_expected_stats,   season, 30)
    grab("sprint",  pyb.statcast_sprint_speed,             season, 10)
    grab("fg_bat",  pyb.batting_stats,  season, qual=30)
    grab("fg_pit",  pyb.pitching_stats, season, qual=10)
    bt = getattr(pyb, "statcast_batter_bat_tracking", None)
    if bt: grab("bat_track", bt, season)
    else: lb["bat_track"] = None
    # FanGraphs-id mapping for everyone we might need
    lb["idmap"] = None
    return lb

def build_idmap(mlbam_ids):
    try:
        df = pyb.playerid_reverse_lookup(list(set(mlbam_ids)), key_type="mlbam")
        return {int(r["key_mlbam"]): r for _, r in df.iterrows()}
    except Exception as e:
        log(f"  ✗ id map unavailable ({type(e).__name__})")
        return {}

def lb_row(df, key_col_candidates, key):
    if df is None: return None
    c = pick_col(df, key_col_candidates)
    if c is None: return None
    m = df[df[c] == key]
    if len(m) == 0: return None
    return m.iloc[0].to_dict()

def fg_row(df, idmap, mlbam_id):
    if df is None: return None
    ent = idmap.get(mlbam_id)
    if ent is None: return None
    fgid = ent.get("key_fangraphs")
    if fgid is None or (isinstance(fgid, float) and math.isnan(fgid)): return None
    c = pick_col(df, ["IDfg", "playerid", "playerId"])
    if c is None: return None
    m = df[df[c] == int(fgid)]
    return m.iloc[0].to_dict() if len(m) else None

# ----------------------------------------------------------------------------
# Per-player Statcast cache
# ----------------------------------------------------------------------------
def season_start(season): return date(season, 3, 15)

def cached_statcast(kind, pid, season, cache_dir, today):
    """kind: 'batter'|'pitcher'. Returns pitch-level DataFrame season-to-date (through yesterday)."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{kind}_{pid}_{season}.csv")
    have_through = None
    df = None
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, low_memory=False)
            if len(df): have_through = date.fromisoformat(str(df["game_date"].max())[:10])
        except Exception:
            df = None
    need_from = season_start(season) if have_through is None else have_through + timedelta(days=1)
    need_to = today - timedelta(days=1)
    if need_from <= need_to:
        try:
            fn = pyb.statcast_batter if kind == "batter" else pyb.statcast_pitcher
            new = fn(need_from.isoformat(), need_to.isoformat(), pid)
            if new is not None and len(new):
                df = pd.concat([df, new], ignore_index=True) if df is not None else new
                df.to_csv(path, index=False)
        except Exception:
            pass
    return df if df is not None else pd.DataFrame()

def spray_theta(row, bat_hand):
    """Spray angle in degrees; negative = pull side for this batter."""
    hx, hy = fnum(row.get("hc_x")), fnum(row.get("hc_y"))
    if hx is None or hy is None: return None
    t = math.degrees(math.atan2(hx - 125.42, 198.27 - hy))  # neg = LF, pos = RF
    return t if bat_hand == "R" else -t  # flip so negative = pull for lefties too

def batter_metrics_from_cache(df, hand, today, season):
    m = {}
    if df is None or len(df) == 0: return m
    df = df.copy()
    df["game_date"] = df["game_date"].astype(str).str[:10]
    bip = df[df["type"] == "X"].copy() if "type" in df else df[df.get("launch_speed").notna()].copy()
    ls, la = bip.get("launch_speed"), bip.get("launch_angle")
    n = len(bip)
    if n >= 5:
        m["avgEV"] = rnd(ls.mean()); m["maxEV"] = rnd(ls.max())
        m["hardHit"] = rnd(100 * (ls >= 95).mean())
        m["laSD"] = rnd(la.std())
        m["sweetSpot"] = rnd(100 * ((la >= 8) & (la <= 32)).mean())
        m["fbPct"] = rnd(100 * (la >= 25).mean())
        if "launch_speed_angle" in bip:
            m["barrel"] = rnd(100 * (bip["launch_speed_angle"] == 6).mean())
        thetas = bip.apply(lambda r: spray_theta(r, hand), axis=1)
        air = la >= 10
        pulled_air = ((thetas < -12) & air)
        m["pullAir"] = rnd(100 * pulled_air.sum() / max(1, air.sum()))
        m["pulledFb"] = rnd(100 * ((thetas < -12) & (la >= 25)).mean())
        m["xhrSeason"] = rnd(sum(xhr_prob(fnum(e), fnum(a)) for e, a in zip(ls, la)), 1)
        m["hrSeasonSC"] = int((bip.get("events") == "home_run").sum()) if "events" in bip else None
        est = pick_col(bip, ["estimated_slg_using_speedangle"])
        if est: m["xslgProxy"] = rnd(bip[est].mean(), 3)
    # plate discipline from all pitches
    if "description" in df and len(df) >= 30:
        desc = df["description"].fillna("")
        swing = desc.isin(["swinging_strike", "swinging_strike_blocked", "foul", "foul_tip",
                           "hit_into_play", "foul_bunt", "missed_bunt", "bunt_foul_tip"])
        whiffs = desc.isin(["swinging_strike", "swinging_strike_blocked", "missed_bunt"])
        m["whiff"] = rnd(100 * whiffs.sum() / max(1, swing.sum()))
        px, pz = df.get("plate_x"), df.get("plate_z")
        szt, szb = df.get("sz_top"), df.get("sz_bot")
        if px is not None and szt is not None:
            in_zone = (px.abs() <= 0.83) & (pz >= szb) & (pz <= szt)
            m["chase"] = rnd(100 * (swing & ~in_zone).sum() / max(1, (~in_zone).sum()))
            m["zoneContact"] = rnd(100 * (swing & in_zone & ~whiffs).sum() / max(1, (swing & in_zone).sum()))
        if "pitch_number" in df and "balls" in df:
            fp = df[(df["balls"] == 0) & (df["strikes"] == 0)]
            fps = fp["description"].fillna("").isin(["swinging_strike", "foul", "hit_into_play", "foul_tip"])
            m["fpSwing"] = rnd(100 * fps.mean()) if len(fp) else None
        # vs pitch buckets
        vsp = {}
        pname = df.get("pitch_name")
        if pname is not None:
            for b in BUCKETS:
                sub = df[pname.map(lambda x: PITCH_BUCKETS.get(x, "Other")) == b]
                if len(sub) < 15:
                    continue
                sd = sub["description"].fillna("")
                sw = sd.isin(["swinging_strike", "swinging_strike_blocked", "foul", "foul_tip", "hit_into_play"])
                wh = sd.isin(["swinging_strike", "swinging_strike_blocked"])
                sbip = sub[sub["type"] == "X"] if "type" in sub else sub[sub["launch_speed"].notna()]
                estc = pick_col(sbip, ["estimated_slg_using_speedangle"])
                slg = rnd(sbip[estc].mean(), 3) if (estc and len(sbip) >= 5) else None
                brl = rnd(100 * (sbip["launch_speed_angle"] == 6).mean()) if ("launch_speed_angle" in sbip and len(sbip) >= 5) else None
                vsp[b] = {"slg": slg, "whiff": rnd(100 * wh.sum() / max(1, sw.sum())), "barrel": brl, "n": int(len(sub))}
        m["vsPitch"] = vsp
        # velocity bands (est SLG on balls in play by pitch velo)
        vb = {}
        if "release_speed" in df:
            for label, lo, hi in [("93-", 0, 92.99), ("93-96", 93, 95.99), ("96+", 96, 200)]:
                sub = bip[(bip["release_speed"] >= lo) & (bip["release_speed"] <= hi)]
                estc = pick_col(sub, ["estimated_slg_using_speedangle"])
                vb[label] = rnd(sub[estc].mean(), 3) if (estc and len(sub) >= 8) else None
        m["veloBands"] = vb
    # rolling by game (last 30 games) + windowed form + batted sample
    if n >= 5:
        bip["gd"] = bip["game_date"]
        estc = pick_col(bip, ["estimated_slg_using_speedangle"])
        gb = bip.groupby("gd")
        games = sorted(gb.groups.keys())[-30:]
        rolling = []
        for i, gd in enumerate(games):
            g = gb.get_group(gd)
            rolling.append({
                "g": i + 1,
                "xslg": rnd(g[estc].mean(), 3) if estc else None,
                "ev": rnd(g["launch_speed"].mean()),
                "barrels": int((g.get("launch_speed_angle") == 6).sum()) if "launch_speed_angle" in g else 0,
            })
        m["rolling"] = rolling
        def window_idx(days):
            cut = (today - timedelta(days=days)).isoformat()
            w = bip[bip["game_date"] >= cut]
            if len(w) < 4: return None
            xs = fnum(w[estc].mean()) if estc else None
            br = 100 * (w.get("launch_speed_angle") == 6).mean() if "launch_speed_angle" in w else 0
            hh = 100 * (w["launch_speed"] >= 95).mean()
            sc = 0.0; parts = 0
            if xs is not None: sc += 0.5 * max(0, min(100, (xs - 0.300) / 0.400 * 100)); parts += 0.5
            sc += 0.3 * max(0, min(100, (br - 4) / 16 * 100)); parts += 0.3
            sc += 0.2 * max(0, min(100, (hh - 30) / 30 * 100)); parts += 0.2
            return int(round(sc / parts))
        m["last30"] = window_idx(30); m["last14"] = window_idx(14); m["last7"] = window_idx(7)
        tail = bip.tail(60)
        batted = []
        for _, r in tail.iterrows():
            th = spray_theta(r, hand)
            ev, ang = fnum(r.get("launch_speed")), fnum(r.get("launch_angle"))
            if th is None or ev is None: continue
            raw = math.degrees(math.atan2(fnum(r.get("hc_x"), 125.42) - 125.42, 198.27 - fnum(r.get("hc_y"), 100)))
            batted.append({
                "theta": rnd(raw), "ev": rnd(ev), "la": rnd(ang),
                "dist": rnd(fnum(r.get("hit_distance_sc"), 0), 0),
                "hr": bool(r.get("events") == "home_run"),
                "barrel": bool(fnum(r.get("launch_speed_angle"), 0) == 6),
            })
        m["batted"] = batted
    return m

def pitcher_metrics_from_cache(df, today):
    m = {}
    if df is None or len(df) == 0: return m
    df = df.copy()
    df["game_date"] = df["game_date"].astype(str).str[:10]
    starts = sorted(df["game_date"].unique())
    last3 = starts[-3:]
    # pitch mix over last 3 outings
    sub = df[df["game_date"].isin(last3)]
    mix = {}
    if "pitch_name" in sub and len(sub):
        counts = sub["pitch_name"].map(lambda x: PITCH_BUCKETS.get(x, "Other")).value_counts(normalize=True)
        for b in BUCKETS:
            pct = int(round(100 * counts.get(b, 0)))
            if pct > 0: mix[b] = pct
    m["mix"] = [{"pitch": k, "pct": v} for k, v in sorted(mix.items(), key=lambda kv: -kv[1])]
    if m["mix"]: m["primary"] = m["mix"][0]["pitch"]
    # fastball velo by start -> trend
    ff = df[df.get("pitch_name").isin(["4-Seam Fastball", "Sinker"])] if "pitch_name" in df else df
    if len(ff) >= 20:
        per = ff.groupby("game_date")["release_speed"].mean()
        per = per.reindex(sorted(per.index))
        vals = list(per.tail(4).values)
        m["fbVelo"] = rnd(per.tail(3).mean())
        if len(vals) >= 3:
            m["veloTrend"] = rnd(vals[-1] - (sum(vals[:-1]) / len(vals[:-1])))
    # pitches per start & rest
    per_start = df.groupby("game_date").size()
    if len(per_start): m["pitchCountExp"] = int(round(per_start.tail(3).mean()))
    if starts:
        m["restDays"] = (today - date.fromisoformat(starts[-1])).days
    # launch angle allowed + hang proxy
    bip = df[df["type"] == "X"] if "type" in df else df[df["launch_speed"].notna()]
    if len(bip) >= 10:
        m["laA"] = rnd(bip["launch_angle"].mean())
    return m

# ----------------------------------------------------------------------------
# Weather (Open-Meteo, no key)
# ----------------------------------------------------------------------------
def game_weather(park, game_dt_utc):
    p = PARKS[park]
    j = fetch_json("https://api.open-meteo.com/v1/forecast", {
        "latitude": p["lat"], "longitude": p["lon"],
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m",
        "temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
        "timeformat": "unixtime", "forecast_days": 3, "past_days": 1,
    })
    out = {"temp": None, "humidity": None, "wind": None, "windDir": "Calm", "roofStatus": "open"}
    if p["roof"] == "retractable":
        out["roofStatus"] = "retractable (assume closed if extreme heat/rain)"
    try:
        hrs = j["hourly"]; times = hrs["time"]
        target = game_dt_utc.timestamp() + 3600  # ~1 hr into the game
        i = min(range(len(times)), key=lambda k: abs(times[k] - target))
        out["temp"] = rnd(hrs["temperature_2m"][i], 0)
        out["humidity"] = rnd(hrs["relative_humidity_2m"][i], 0)
        spd = rnd(hrs["wind_speed_10m"][i], 0)
        wdir = fnum(hrs["wind_direction_10m"][i])  # direction wind comes FROM
        out["wind"] = spd
        if spd is not None and spd < 4:
            out["windDir"] = "Calm"
        elif wdir is not None:
            toward = (wdir + 180) % 360
            rel = ((toward - p["cf"]) + 180) % 360 - 180  # 0 = straight out to CF
            a = abs(rel)
            side = "LF" if rel < 0 else "RF"
            if a <= 30: out["windDir"] = "Out to CF"
            elif a <= 75: out["windDir"] = f"Out to {side}"
            elif a < 105: out["windDir"] = f"Cross {'L→R' if rel > 0 else 'R→L'}"
            elif a <= 150: out["windDir"] = f"In from {side}"
            else: out["windDir"] = "In from CF"
        cov("weather", True)
    except Exception:
        cov("weather", False)
    return out

# ----------------------------------------------------------------------------
# Builders
# ----------------------------------------------------------------------------
def build_pitcher(pid, team, info, lb, idmap, cache_dir, season, today):
    name = info.get(pid, {}).get("name", f"#{pid}")
    hand = info.get(pid, {}).get("throw", "R")
    fg = fg_row(lb["fg_pit"], idmap, pid)
    sev = lb_row(lb["pit_ev"], ["player_id", "pitcher", "id"], pid)
    sx = lb_row(lb["pit_x"], ["player_id", "pitcher", "id"], pid)
    sc = cached_statcast("pitcher", pid, season, cache_dir, today)
    scm = pitcher_metrics_from_cache(sc, today)
    cov("pitcher_fg", fg is not None); cov("pitcher_savant", sev is not None)
    p = {
        "id": pid, "name": name, "team": team, "hand": hand,
        "hr9":  row_val(fg, lb["fg_pit"], ["HR/9"], None),
        "fip":  row_val(fg, lb["fg_pit"], ["FIP"], None),
        "xfip": row_val(fg, lb["fg_pit"], ["xFIP"], None),
        "siera": row_val(fg, lb["fg_pit"], ["SIERA"], None),
        "gb":   row_val(fg, lb["fg_pit"], ["GB%"], None),
        "fb":   row_val(fg, lb["fg_pit"], ["FB%"], None),
        "hrFbA": row_val(fg, lb["fg_pit"], ["HR/FB"], None),
        "k":    row_val(fg, lb["fg_pit"], ["K%"], None),
        "bb":   row_val(fg, lb["fg_pit"], ["BB%"], None),
        "swstr": row_val(fg, lb["fg_pit"], ["SwStr%"], None),
        "zone": row_val(fg, lb["fg_pit"], ["Zone%"], None),
        "fStrike": row_val(fg, lb["fg_pit"], ["F-Strike%"], None),
        "stuff": row_val(fg, lb["fg_pit"], ["Stuff+", "Stf+", "sp_stuff"], None),
        "loc":   row_val(fg, lb["fg_pit"], ["Location+", "Loc+", "sp_location"], None),
        "pitchingPlus": row_val(fg, lb["fg_pit"], ["Pitching+", "Pit+", "sp_pitching"], None),
        "barrelA": row_val(sev, lb["pit_ev"], ["brl_percent", "barrel_batted_rate"], None),
        "hardHitA": row_val(sev, lb["pit_ev"], ["ev95percent", "hard_hit_percent", "ev95plus_percent"], None),
        "evA": row_val(sev, lb["pit_ev"], ["avg_hit_speed", "exit_velocity_avg"], None),
        "xera": row_val(sx, lb["pit_x"], ["xera", "est_era"], None),
        "laA": scm.get("laA") or row_val(sev, lb["pit_ev"], ["avg_hit_angle"], None),
        "fbVelo": scm.get("fbVelo"),
        "veloTrend": scm.get("veloTrend"),
        "pitchCountExp": scm.get("pitchCountExp"),
        "restDays": scm.get("restDays"),
        "mix": scm.get("mix", []),
        "primary": scm.get("primary"),
        "strike": None,
    }
    # percentages that FanGraphs returns as 0-1 fractions -> convert
    for k in ["gb", "fb", "hrFbA", "k", "bb", "swstr", "zone", "fStrike"]:
        v = p[k]
        if v is not None and v <= 1.0: p[k] = rnd(v * 100)
    return p

def build_bullpen(team, team_id, starter_id, info, lb, idmap, today):
    usage = recent_reliever_pitches(team_id, today)
    pids = [p for p in roster_pitchers(team_id) if p != starter_id]
    fgd = lb["fg_pit"]
    rows = []
    for pid in pids:
        fg = fg_row(fgd, idmap, pid)
        if fg is None: continue
        gs = row_val(fg, fgd, ["GS"], 0) or 0
        g = row_val(fg, fgd, ["G"], 0) or 0
        ip = row_val(fg, fgd, ["IP"], 0) or 0
        if g and gs / max(g, 1) > 0.5:  # mostly a starter
            continue
        rows.append((pid, fg, ip))
    rows.sort(key=lambda r: -r[2])
    def wavg(key_opts):
        num = den = 0.0
        for pid, fg, ip in rows:
            v = row_val(fg, fgd, key_opts, None)
            if v is None: continue
            if v <= 1.0 and key_opts[0].endswith("%"): v *= 100
            num += v * ip; den += ip
        return rnd(num / den) if den else None
    yest = sum(v.get(1, 0) for v in usage.values())
    three = sum(sum(v.values()) for v in usage.values())
    workload = int(max(0, min(100, three / 3.0)))  # ~300 pitches over 3 days = maxed
    high_lev = any(v.get(1, 0) >= 15 for v in usage.values())
    arms = []
    for pid, fg, ip in rows[:3]:
        arms.append({"name": info.get(pid, {}).get("name", f"#{pid}"),
                     "hand": info.get(pid, {}).get("throw", "R"), "tag": ""})
    cov("bullpen", len(rows) > 0)
    return {
        "team": team,
        "hr9": wavg(["HR/9"]), "barrelA": wavg(["Barrel%"]),
        "hardHitA": wavg(["HardHit%", "Hard%"]), "velo": wavg(["FBv", "vFA (pi)", "vFA"]),
        "workload": workload, "pitchesYesterday": int(yest),
        "highLevYesterday": bool(high_lev), "likelyArms": arms,
    }

def build_hitter(pid, team, order, info, opp_pitcher_id, lb, idmap, cache_dir, season, today, quick):
    inf = info.get(pid, {})
    name, hand = inf.get("name", f"#{pid}"), inf.get("bat", "R")
    fg = fg_row(lb["fg_bat"], idmap, pid)
    sev = lb_row(lb["bat_ev"], ["player_id", "batter", "id"], pid)
    sx = lb_row(lb["bat_x"], ["player_id", "batter", "id"], pid)
    spr = lb_row(lb["sprint"], ["player_id", "runner_id", "id"], pid)
    bt = lb_row(lb["bat_track"], ["player_id", "batter", "id"], pid) if lb.get("bat_track") is not None else None
    sc = cached_statcast("batter", pid, season, cache_dir, today)
    scm = batter_metrics_from_cache(sc, hand, today, season)
    cov("hitter_fg", fg is not None); cov("hitter_statcast", len(sc) > 0)
    h = {
        "id": f"{team}-{pid}", "pid": pid, "team": team, "name": name, "hand": hand, "order": order,
        "barrel": scm.get("barrel") or row_val(sev, lb["bat_ev"], ["brl_percent", "barrel_batted_rate"], None),
        "barrelPA": row_val(sev, lb["bat_ev"], ["brl_pa", "barrels_per_pa"], None),
        "hardHit": scm.get("hardHit") or row_val(sev, lb["bat_ev"], ["ev95percent", "hard_hit_percent"], None),
        "sweetSpot": scm.get("sweetSpot"),
        "avgEV": scm.get("avgEV") or row_val(sev, lb["bat_ev"], ["avg_hit_speed", "exit_velocity_avg"], None),
        "maxEV": scm.get("maxEV") or row_val(sev, lb["bat_ev"], ["max_hit_speed"], None),
        "batSpeed": row_val(bt, lb.get("bat_track"), ["avg_bat_speed", "bat_speed"], None) if bt else None,
        "pullAir": scm.get("pullAir"), "fbPct": scm.get("fbPct"), "pulledFb": scm.get("pulledFb"),
        "hrFb": row_val(fg, lb["fg_bat"], ["HR/FB"], None),
        "iso": row_val(fg, lb["fg_bat"], ["ISO"], None),
        "slg": row_val(fg, lb["fg_bat"], ["SLG"], None) or scm.get("xslgProxy"),
        "xslg": row_val(sx, lb["bat_x"], ["est_slg", "xslg"], None) or scm.get("xslgProxy"),
        "xwoba": row_val(sx, lb["bat_x"], ["est_woba", "xwoba"], None),
        "laSD": scm.get("laSD"),
        "chase": scm.get("chase"), "whiff": scm.get("whiff"),
        "zoneContact": scm.get("zoneContact"), "fpSwing": scm.get("fpSwing"),
        "sprint": row_val(spr, lb["sprint"], ["sprint_speed", "hp_to_1b"], None),
        "last30": scm.get("last30"), "last14": scm.get("last14"), "last7": scm.get("last7"),
        "vsPitch": scm.get("vsPitch", {}), "veloBands": scm.get("veloBands", {}),
        "rolling": scm.get("rolling", []), "batted": scm.get("batted", []),
        "xhrSeason": scm.get("xhrSeason"),
        "hrSeason": row_val(fg, lb["fg_bat"], ["HR"], None) or scm.get("hrSeasonSC"),
        "careerVsP": {"pa": 0, "hr": 0, "slg": None},
    }
    v = h["hrFb"]
    if v is not None and v <= 1.0: h["hrFb"] = rnd(v * 100)
    if h["hrSeason"] is not None: h["hrSeason"] = int(h["hrSeason"])
    if not quick and opp_pitcher_id:
        h["careerVsP"] = bvp(pid, opp_pitcher_id)
        time.sleep(0.15)
    return h

# ----------------------------------------------------------------------------
# Demo slate (offline sanity check for the app)
# ----------------------------------------------------------------------------
def demo_slate(d):
    random.seed(42)
    parks = ["CIN", "NYY", "COL", "SF"]
    matchups = [("PHI", "CIN"), ("BAL", "NYY"), ("LAD", "COL"), ("BOS", "SF")]
    games, pitchers, bullpens, hitters = [], {}, {}, []
    first = ["A.", "B.", "C.", "D.", "E.", "F.", "G.", "H.", "J."]
    last = ["Marlowe", "Ostrander", "Whitfield", "Delacroix", "Vasquez", "Stanhope", "Nakashima",
            "Beaumont", "Winslow", "Calderón", "Ellingham", "Fontaine", "Kessler", "Trevelyan",
            "Aldana", "Holloway", "Ridley", "Volkov"]
    for gi, (away, home) in enumerate(matchups):
        pk = parks[gi]
        games.append({"id": f"G{gi+1}", "away": away, "home": home, "park": pk,
                      "time": ["1:10 PM", "7:05 PM", "8:40 PM", "9:45 PM"][gi],
                      "temp": random.randint(58, 94), "wind": random.randint(3, 16),
                      "windDir": random.choice(["Out to LF", "Out to CF", "Out to RF", "In from RF", "Cross L→R"]),
                      "humidity": random.randint(25, 80), "roofStatus": "open",
                      "status": "Scheduled",
                      "lineupStatus": {away: "projected (last game)", home: "confirmed"}})
        for t in (away, home):
            mix = [{"pitch": "4-Seam", "pct": 42}, {"pitch": "Slider", "pct": 26},
                   {"pitch": "Changeup", "pct": 18}, {"pitch": "Curve", "pct": 14}]
            pitchers[t] = {"id": 0, "name": f"{random.choice(first)} {random.choice(last)}", "team": t,
                           "hand": random.choice(["R", "R", "L"]),
                           "hr9": round(random.uniform(0.7, 2.1), 2), "xera": round(random.uniform(2.8, 5.9), 2),
                           "fip": round(random.uniform(3.0, 5.6), 2), "xfip": round(random.uniform(3.1, 5.3), 2),
                           "siera": round(random.uniform(3.1, 5.2), 2),
                           "barrelA": round(random.uniform(4.5, 12.5), 1), "hardHitA": round(random.uniform(33, 48), 1),
                           "evA": round(random.uniform(86.5, 91.5), 1), "laA": round(random.uniform(9, 17), 1),
                           "gb": round(random.uniform(32, 52), 1), "fb": round(random.uniform(28, 45), 1),
                           "hrFbA": round(random.uniform(7, 18), 1), "fbVelo": round(random.uniform(91.5, 98), 1),
                           "veloTrend": round(random.uniform(-1.6, 0.7), 1),
                           "stuff": random.randint(88, 114), "loc": random.randint(90, 110), "pitchingPlus": random.randint(90, 112),
                           "k": round(random.uniform(17, 31), 1), "bb": round(random.uniform(5, 11), 1),
                           "swstr": round(random.uniform(8, 15), 1), "zone": round(random.uniform(41, 51), 1),
                           "fStrike": round(random.uniform(56, 67), 1), "strike": None,
                           "pitchCountExp": random.randint(80, 98), "restDays": random.randint(4, 6),
                           "mix": mix, "primary": "4-Seam"}
            bullpens[t] = {"team": t, "hr9": round(random.uniform(0.8, 1.8), 2),
                           "barrelA": round(random.uniform(5, 11), 1), "hardHitA": round(random.uniform(34, 46), 1),
                           "velo": round(random.uniform(93, 97), 1), "workload": random.randint(10, 90),
                           "pitchesYesterday": random.randint(0, 60), "highLevYesterday": random.random() < 0.4,
                           "likelyArms": [{"name": "Demo Arm", "hand": random.choice(["R", "L"]), "tag": ""} for _ in range(3)]}
            for o in range(1, 10):
                power = random.uniform(0.2, 1)
                nm = f"{random.choice(first)} {random.choice(last)}"
                rolling = []
                base = 0.30 + power * 0.25
                for g in range(30):
                    base = min(0.75, max(0.25, base + random.uniform(-0.03, 0.03)))
                    rolling.append({"g": g + 1, "xslg": round(base, 3), "ev": round(random.uniform(86, 94), 1), "barrels": random.randint(0, 3)})
                batted = []
                for _ in range(46):
                    ev = random.uniform(64, 106 + power * 10); la = random.uniform(-15, 48)
                    dist = max(0, (ev - 55) * 5.0 * max(0.15, math.sin(max(5, min(45, la)) / 45 * math.pi / 2)))
                    batted.append({"theta": round(random.uniform(-40, 40), 1), "ev": round(ev, 1), "la": round(la, 1),
                                   "dist": int(dist), "hr": dist > 372 and 18 < la < 42,
                                   "barrel": ev >= 98 and 24 <= la <= 36})
                hitters.append({"id": f"{t}-{o}", "pid": 0, "team": t, "name": nm,
                                "hand": random.choice(["R", "R", "L", "S"]), "order": o,
                                "barrel": round(4 + power * 15, 1), "barrelPA": round(2 + power * 8, 1),
                                "hardHit": round(31 + power * 26, 1), "sweetSpot": round(random.uniform(29, 41), 1),
                                "avgEV": round(86 + power * 8, 1), "maxEV": round(105 + power * 13, 1),
                                "batSpeed": round(67 + power * 11, 1), "pullAir": round(random.uniform(12, 38), 1),
                                "fbPct": round(random.uniform(22, 48), 1), "pulledFb": round(random.uniform(4, 15), 1),
                                "hrFb": round(6 + power * 22, 1), "iso": round(0.09 + power * 0.25, 3),
                                "slg": round(0.34 + power * 0.28 + random.uniform(-0.05, 0.05), 3),
                                "xslg": round(0.35 + power * 0.29, 3), "xwoba": round(0.28 + power * 0.14, 3),
                                "laSD": round(random.uniform(12, 25), 1), "chase": round(random.uniform(20, 37), 1),
                                "whiff": round(random.uniform(16, 37), 1), "zoneContact": round(random.uniform(76, 92), 1),
                                "fpSwing": round(random.uniform(20, 44), 1), "sprint": round(random.uniform(25.5, 29.8), 1),
                                "last30": random.randint(20, 96), "last14": random.randint(15, 99), "last7": random.randint(10, 99),
                                "vsPitch": {b: {"slg": round(random.uniform(0.30, 0.72), 3),
                                                "whiff": round(random.uniform(14, 40), 1),
                                                "barrel": round(random.uniform(3, 18), 1), "n": 60} for b in BUCKETS},
                                "veloBands": {"93-": round(random.uniform(0.35, 0.62), 3),
                                              "93-96": round(random.uniform(0.33, 0.60), 3),
                                              "96+": round(random.uniform(0.28, 0.55), 3)},
                                "rolling": rolling, "batted": batted,
                                "xhrSeason": round(6 + power * 30, 1), "hrSeason": int(5 + power * 28 + random.uniform(-4, 2)),
                                "careerVsP": {"pa": random.randint(0, 25), "hr": random.randint(0, 3),
                                              "slg": round(random.uniform(0.3, 0.75), 3)}})
    return {"generatedAt": datetime.now(timezone.utc).isoformat(), "date": d.isoformat(),
            "demo": True, "parks": PARKS, "games": games, "pitchers": pitchers,
            "bullpens": bullpens, "hitters": hitters}

# ----------------------------------------------------------------------------
# Main build
# ----------------------------------------------------------------------------
def build(d, out_path, cache_dir, quick=False):
    season = d.year
    log(f"Building slate for {d.isoformat()} (season {season})")
    sched = get_schedule(d)
    if not sched:
        log("No MLB games found for this date."); return False
    log(f"{len(sched)} games on the schedule")

    lb = load_leaderboards(season)

    # collect every player id we need
    all_pids = []
    game_meta = []
    for g in sched:
        home_lu = lineup_from_schedule(g, "home")
        away_lu = lineup_from_schedule(g, "away")
        lu_status = {}
        if home_lu: lu_status[g["home"]] = "confirmed"
        else:
            home_lu = last_lineup(g["home_id"], d); lu_status[g["home"]] = "projected (last game)" if home_lu else "unavailable"
        if away_lu: lu_status[g["away"]] = "confirmed"
        else:
            away_lu = last_lineup(g["away_id"], d); lu_status[g["away"]] = "projected (last game)" if away_lu else "unavailable"
        game_meta.append({**g, "home_lu": home_lu, "away_lu": away_lu, "lu_status": lu_status})
        all_pids += home_lu + away_lu + [g["probables"]["home"], g["probables"]["away"]]
        cov("lineup_confirmed", bool(lineup_from_schedule(g, "home")))
        cov("lineup_confirmed", bool(lineup_from_schedule(g, "away")))
        cov("probable_pitcher", bool(g["probables"]["home"]))
        cov("probable_pitcher", bool(g["probables"]["away"]))

    info = people_info(all_pids)
    idmap = build_idmap([p for p in all_pids if p])
    log(f"Resolved {len(info)} players, {len(idmap)} FanGraphs id matches")

    games, pitchers, bullpens, hitters = [], {}, {}, []
    for g in game_meta:
        park = g["home"] if g["home"] in PARKS else None
        if park is None: continue
        gdt = datetime.fromisoformat(g["gameDate"].replace("Z", "+00:00"))
        wx = game_weather(park, gdt)
        local_hint = gdt.astimezone().strftime("%I:%M %p").lstrip("0")  # viewer's local time
        games.append({"id": f"G{g['gamePk']}", "gamePk": g["gamePk"], "away": g["away"], "home": g["home"],
                      "park": park, "time": local_hint, "status": g["status"],
                      "lineupStatus": g["lu_status"], **wx})
        for side in ("home", "away"):
            team = g[side]; team_id = g[f"{side}_id"]
            spid = g["probables"][side]
            if spid:
                log(f"  {team}: starter {info.get(spid, {}).get('name', spid)}")
                pitchers[team] = build_pitcher(spid, team, info, lb, idmap, cache_dir, season, d)
            else:
                pitchers[team] = {"id": None, "name": "TBD", "team": team, "hand": "R", "mix": [], "primary": None}
                log(f"  {team}: starter TBD")
            bullpens[team] = build_bullpen(team, team_id, spid, info, lb, idmap, d)
        for side in ("home", "away"):
            team = g[side]
            opp = g["away"] if side == "home" else g["home"]
            opp_pid = pitchers[opp].get("id")
            lu = g[f"{side}_lu"]
            for order, pid in enumerate(lu, 1):
                log(f"    hitter {order}: {info.get(pid, {}).get('name', pid)} ({team})")
                hitters.append(build_hitter(pid, team, order, info, opp_pid, lb, idmap, cache_dir, season, d, quick))

    slate = {"generatedAt": datetime.now(timezone.utc).isoformat(), "date": d.isoformat(),
             "demo": False, "parks": PARKS, "games": games, "pitchers": pitchers,
             "bullpens": bullpens, "hitters": hitters}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w") as f: json.dump(slate, f, default=str)
    os.replace(tmp, out_path)
    log(f"Wrote {out_path} — {len(games)} games, {len(hitters)} hitters")
    log("Coverage (ok/missing): " + ", ".join(f"{k} {v[0]}/{v[0]+v[1]}" for k, v in sorted(COVERAGE.items())))
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default today)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "slate.json"))
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache"))
    ap.add_argument("--loop", type=int, help="rebuild every N minutes")
    ap.add_argument("--demo", action="store_true", help="write a fake slate (no internet)")
    ap.add_argument("--quick", action="store_true", help="skip batter-vs-pitcher lookups")
    args = ap.parse_args()
    d = date.fromisoformat(args.date) if args.date else date.today()

    if args.demo:
        slate = demo_slate(d)
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f: json.dump(slate, f, default=str)
        log(f"Wrote DEMO slate to {args.out}")
        return

    if not HAVE_PYB:
        print("pybaseball is required for real data:  pip install pybaseball"); sys.exit(1)

    while True:
        try:
            COVERAGE.clear()
            build(d, args.out, args.cache, quick=args.quick)
        except KeyboardInterrupt:
            raise
        except Exception:
            log("Build failed:"); traceback.print_exc()
        if not args.loop:
            break
        log(f"Sleeping {args.loop} min… (Ctrl-C to stop)")
        time.sleep(args.loop * 60)
        d = date.fromisoformat(args.date) if args.date else date.today()

if __name__ == "__main__":
    main()
