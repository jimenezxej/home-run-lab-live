#!/usr/bin/env python3
"""
Home Run Lab 8.0 — Attach season stats by identity map.

Reads data/player-identity-map.json and attaches stats by MLBAM playerId.
"""
from pathlib import Path
import json, datetime as dt, urllib.request, time

ROOT = Path.cwd()
DATA = ROOT / "data"
SEASON = dt.date.today().year
PEOPLE_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting&season={season}&gameType=R"

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=35) as r:
        return json.loads(r.read().decode("utf-8"))

def load(path, fallback):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: return fallback
    return fallback

def save(path, obj):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def to_int(v):
    try:
        if v in (None, ""): return None
        return int(float(str(v).replace(",", "")))
    except Exception: return None

def to_float(v):
    try:
        if v in (None, ""): return None
        return float(v)
    except Exception: return None

def fetch_hitting_stats(pid):
    data = fetch_json(PEOPLE_STATS_URL.format(player_id=pid, season=SEASON))
    stats = data.get("stats", [])
    splits = stats[0].get("splits", []) if stats else []
    if not splits:
        return None, "no_season_hitting_split"
    stat = splits[0].get("stat", {}) or {}
    avg = to_float(stat.get("avg"))
    slg = to_float(stat.get("slg"))
    iso = round(slg - avg, 3) if avg is not None and slg is not None else None
    return {
        "pa": to_int(stat.get("plateAppearances")),
        "ab": to_int(stat.get("atBats")),
        "h": to_int(stat.get("hits")),
        "hr": to_int(stat.get("homeRuns")),
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
        "iso": iso,
        "gamesPlayed": to_int(stat.get("gamesPlayed"))
    }, "verified_player_id_season_stats"

def main():
    slate_path = DATA / "slate.json"
    if not slate_path.exists():
        slate_path = ROOT / "app" / "slate.json"
    slate = load(slate_path, {"hitters": []})
    identity = load(DATA / "player-identity-map.json", {"identities": {}})
    identities = identity.get("identities", {})

    mapped, missing, suspicious = [], [], []
    cache = {}

    for h in slate.get("hitters", []) or []:
        key = f"{h.get('team')}|{h.get('name')}"
        ident = identities.get(key)
        if not ident or not ident.get("resolved"):
            h["identityResolved"] = False
            h["identityTrusted"] = False
            h["seasonStatsVerified"] = False
            h["seasonStatsMethod"] = "identity_unresolved"
            h["pa"], h["ab"], h["h"], h["hr"] = 0, 0, 0, 0
            missing.append({"name": h.get("name"), "team": h.get("team"), "reason": "identity_unresolved"})
            continue

        pid = str(ident.get("playerId"))
        if pid in cache:
            stats, stat_method = cache[pid]
        else:
            try:
                stats, stat_method = fetch_hitting_stats(pid)
                cache[pid] = (stats, stat_method)
                time.sleep(.03)
            except Exception as e:
                stats, stat_method = None, f"stats_fetch_error:{e}"

        h["identityResolved"] = True
        h["identityTrusted"] = bool(ident.get("trusted"))
        h["identityMethod"] = ident.get("method")
        h["identitySuspicious"] = bool(ident.get("suspicious"))
        h["playerId"] = ident.get("playerId")
        h["resolvedMlbName"] = ident.get("resolvedMlbName")
        h["resolvedCurrentTeam"] = ident.get("resolvedCurrentTeam")

        if not stats:
            h["seasonStatsVerified"] = False
            h["seasonStatsMethod"] = stat_method
            h["pa"], h["ab"], h["h"], h["hr"] = 0, 0, 0, 0
            missing.append({"name": h.get("name"), "team": h.get("team"), "playerId": pid, "resolved": ident.get("resolvedMlbName"), "reason": stat_method})
            continue

        for k, v in stats.items():
            h[k] = v
        h["seasonStatsVerified"] = True
        h["seasonStatsSource"] = "MLB Stats API player season hitting stats by MLBAM ID"
        h["seasonStatsMethod"] = stat_method
        h["seasonStatsSeason"] = SEASON
        row = {"name": h.get("name"), "team": h.get("team"), "resolved": ident.get("resolvedMlbName"), "playerId": pid, "pa": h.get("pa"), "h": h.get("h"), "hr": h.get("hr"), "trusted": h.get("identityTrusted")}
        mapped.append(row)
        if h.get("identitySuspicious"):
            suspicious.append(row)

    slate["hitters"] = slate.get("hitters", [])
    slate["identityArchitectureVersion"] = "8.0"
    slate["verifiedSeasonStatsAttachedAt"] = dt.datetime.now().isoformat()
    save(DATA / "slate.json", slate)
    if (ROOT / "app").exists():
        save(ROOT / "app" / "slate.json", slate)

    out = {"version":"8.0","updatedAt":dt.datetime.now().isoformat(),"mappedCount":len(mapped),"missingCount":len(missing),"suspiciousAttachedCount":len(suspicious),"mapped":mapped,"missing":missing,"suspiciousAttached":suspicious}
    save(DATA / "hitter-season-map.json", out)
    print(f"Attached by ID: {len(mapped)} mapped / {len(missing)} missing / {len(suspicious)} suspicious")

if __name__ == "__main__":
    main()
