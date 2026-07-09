#!/usr/bin/env python3
"""
Attach verified MLB season stats to current slate hitters.
Stronger matching for team aliases and accented names.
"""
from pathlib import Path
import json, datetime as dt, unicodedata

ROOT = Path.cwd()
DATA = ROOT / "data"

TEAM_ALIASES = {
    "CHW": "CWS", "CWS": "CWS",
    "WSN": "WSH", "WSH": "WSH",
    "AZ": "ARI", "ARI": "ARI",
    "SDP": "SD", "SD": "SD",
    "SFG": "SF", "SF": "SF",
    "TBR": "TB", "TB": "TB",
    "KCR": "KC", "KC": "KC",
    "NYA": "NYY", "NYY": "NYY",
    "NYN": "NYM", "NYM": "NYM",
    "OAK": "ATH", "ATH": "ATH",
}

def load(path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback

def save(path, obj):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

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

def get_direct_id(h):
    for k in ["id", "playerId", "mlbId", "personId"]:
        v = h.get(k)
        if v:
            return str(v)
    return None

def choose_match(hitter, verified):
    players = verified.get("players", {})
    name_index = verified.get("nameIndex", {})
    team_name_index = verified.get("teamNameIndex", {})

    direct = get_direct_id(hitter)
    if direct and direct in players:
        return players[direct], "direct_player_id"

    name_key = norm_name(hitter.get("name"))
    team = norm_team(hitter.get("team"))

    if team and name_key:
        ids = team_name_index.get(f"{team}|{name_key}", [])
        if ids:
            return players[ids[0]], "team_name_match"

    ids = name_index.get(name_key, [])
    if ids:
        return players[ids[0]], "name_match_highest_pa"

    # Last resort: try last-name + first initial when names differ slightly.
    parts = name_key.split()
    if len(parts) >= 2:
        first_initial = parts[0][0]
        last = parts[-1]
        candidates = []
        for pid, p in players.items():
            pk = p.get("nameKey", "")
            pp = pk.split()
            if len(pp) >= 2 and pp[0].startswith(first_initial) and pp[-1] == last:
                if not team or p.get("team") == team:
                    candidates.append(pid)
        if candidates:
            candidates.sort(key=lambda pid: players.get(pid, {}).get("pa") or 0, reverse=True)
            return players[candidates[0]], "fuzzy_initial_last_team_match"

    return None, "no_match"

def attach_fields(h, m, method):
    h["playerId"] = m.get("playerId")
    for key in ["pa","ab","h","hr","doubles","triples","bb","so","avg","obp","slg","ops","iso"]:
        h[key] = m.get(key)
    h["seasonStatsVerified"] = True
    h["seasonStatsSource"] = m.get("source")
    h["seasonStatsMethod"] = method
    h["seasonStatsSeason"] = m.get("season")
    return h

def main():
    slate_path = DATA / "slate.json"
    if not slate_path.exists():
        slate_path = ROOT / "app" / "slate.json"
    if not slate_path.exists():
        raise SystemExit("Missing data/slate.json or app/slate.json")

    slate = load(slate_path, {})
    verified = load(DATA / "verified-hitter-season-stats.json", {"players": {}, "nameIndex": {}, "teamNameIndex": {}})

    mapped, unmapped = [], []
    for h in slate.get("hitters", []) or []:
        match, method = choose_match(h, verified)
        if match:
            attach_fields(h, match, method)
            mapped.append({
                "name": h.get("name"), "team": h.get("team"), "playerId": h.get("playerId"),
                "pa": h.get("pa"), "h": h.get("h"), "hr": h.get("hr"), "method": method
            })
        else:
            h["pa"] = h.get("pa") or 0
            h["ab"] = h.get("ab") or 0
            h["h"] = h.get("h") or 0
            h["hr"] = h.get("hr") or 0
            h["seasonStatsVerified"] = False
            h["seasonStatsSource"] = None
            h["seasonStatsMethod"] = method
            unmapped.append({"name": h.get("name"), "team": h.get("team"), "method": method})

    slate["verifiedSeasonStatsAttachedAt"] = dt.datetime.now().isoformat()
    slate["verifiedSeasonStatsSource"] = verified.get("source")
    slate["verifiedSeasonStatsVersion"] = "6.0.1"

    save(DATA / "slate.json", slate)
    app_dir = ROOT / "app"
    if app_dir.exists():
        save(app_dir / "slate.json", slate)

    out = {
        "version": "6.0.1",
        "updatedAt": dt.datetime.now().isoformat(),
        "mappedCount": len(mapped),
        "unmappedCount": len(unmapped),
        "mapped": mapped,
        "unmapped": unmapped
    }
    save(DATA / "hitter-season-map.json", out)
    print(f"Attached verified season stats: {len(mapped)} mapped / {len(unmapped)} unmapped")
    zero = [m for m in mapped if not m.get("pa")]
    if zero:
        print(f"WARNING: {len(zero)} mapped hitters still have 0/blank PA")

if __name__ == "__main__":
    main()
