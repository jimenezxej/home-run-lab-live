#!/usr/bin/env python3
"""
Home Run Lab 8.0 — Player Identity Map

Builds data/player-identity-map.json.

Purpose:
- Assign every slate hitter a stable MLBAM player ID when possible.
- Detect unsafe name matches.
- Apply known manual overrides.
- Stop the app from silently trusting wrong matches.

This is not the final cloud database yet; it is the local identity foundation.
"""
from pathlib import Path
import json, datetime as dt, urllib.request, unicodedata
from difflib import SequenceMatcher

ROOT = Path.cwd()
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
SEASON = dt.date.today().year

SPORT_PLAYERS_URL = "https://statsapi.mlb.com/api/v1/sports/1/players?season={season}"

TEAM_ALIASES = {
    "CHW":"CWS","CWS":"CWS","WSN":"WSH","WSH":"WSH","AZ":"ARI","ARI":"ARI",
    "SDP":"SD","SD":"SD","SFG":"SF","SF":"SF","TBR":"TB","TB":"TB",
    "KCR":"KC","KC":"KC","NYA":"NYY","NYY":"NYY","NYN":"NYM","NYM":"NYM",
    "OAK":"ATH","ATH":"ATH"
}
SUFFIXES = {"jr","sr","ii","iii","iv","v"}

DANGEROUS_LAST_NAMES = {
    "smith","young","winn","armstrong","diaz","díaz","hoppe","lowe","martin","jackson",
    "sosa","lee","perez","pérez","rodriguez","rodríguez","hernandez","hernández",
    "garcia","garcía","gonzalez","gonzález","de","cruz"
}

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))

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

def clean_tokens(name):
    s = strip_accents(name or "").lower()
    for ch in [".", ",", "'", "’", "-", "_"]:
        s = s.replace(ch, " ")
    return [t for t in s.split() if t]

def norm_name(name):
    return " ".join(clean_tokens(name))

def name_parts(name):
    raw = name or ""
    toks = clean_tokens(raw)
    if not toks:
        return {"full":"", "firstInitial":None, "last":"", "suffix":None}

    # Special handling: De La Cruz, E should last = de la cruz, initial=e.
    if "," in raw:
        left, right = raw.split(",", 1)
        left_tokens = clean_tokens(left)
        right_tokens = clean_tokens(right)
        if left_tokens:
            return {
                "full": norm_name(raw),
                "firstInitial": right_tokens[0][0] if right_tokens else None,
                "last": " ".join(left_tokens),
                "suffix": None
            }

    suffix = toks[-1] if toks[-1] in SUFFIXES else None
    core = toks[:-1] if suffix else toks[:]
    if len(core) == 1:
        return {"full":norm_name(raw), "firstInitial":None, "last":core[0], "suffix":suffix}
    return {"full":norm_name(raw), "firstInitial":core[0][0], "last":core[-1], "suffix":suffix}

def norm_team(t):
    if not t:
        return None
    t = str(t).upper().strip()
    return TEAM_ALIASES.get(t, t)

def get_players():
    cache = DATA / "mlb-sports-players-cache.json"
    if cache.exists():
        cached = load(cache, {})
        if cached.get("season") == SEASON and len(cached.get("people", [])) > 1000:
            return cached["people"]
    data = fetch_json(SPORT_PLAYERS_URL.format(season=SEASON))
    people = data.get("people", [])
    save(cache, {"season": SEASON, "updatedAt": dt.datetime.now().isoformat(), "people": people})
    return people

def build_indexes(people):
    by_id, by_full, by_last_initial, by_last, by_last_suffix = {}, {}, {}, {}, {}
    for p in people:
        pid = p.get("id")
        name = p.get("fullName")
        if not pid or not name:
            continue
        parts = name_parts(name)
        row = {
            "playerId": int(pid),
            "name": name,
            "nameKey": parts["full"],
            "firstInitial": parts["firstInitial"],
            "last": parts["last"],
            "suffix": parts["suffix"],
            "primaryPosition": ((p.get("primaryPosition") or {}).get("abbreviation")),
            "currentTeam": norm_team(((p.get("currentTeam") or {}).get("abbreviation"))),
            "raw": p
        }
        by_id[str(pid)] = row
        by_full.setdefault(row["nameKey"], []).append(row)
        if row["last"] and row["firstInitial"]:
            by_last_initial.setdefault(f"{row['last']}|{row['firstInitial']}", []).append(row)
        if row["last"]:
            by_last.setdefault(row["last"], []).append(row)
        if row["last"] and row["suffix"]:
            by_last_suffix.setdefault(f"{row['last']}|{row['suffix']}", []).append(row)
    return by_id, by_full, by_last_initial, by_last, by_last_suffix

def choose(candidates, team=None, allow_unsafe=False):
    candidates = candidates or []
    if not candidates:
        return None, "no_candidates"

    nt = norm_team(team)
    same = [c for c in candidates if nt and c.get("currentTeam") == nt]
    if len(same) == 1:
        return same[0], "team_match"
    if len(same) > 1:
        return same[0], "multi_team_match_first"

    if len(candidates) == 1:
        return candidates[0], "unique"

    if allow_unsafe:
        return candidates[0], "unsafe_duplicate_first"

    return None, "ambiguous_duplicate"

def override_key(h):
    return f"{norm_team(h.get('team'))}|{h.get('name')}"

def resolve(hitter, indexes, overrides):
    by_id, by_full, by_last_initial, by_last, by_last_suffix = indexes
    team = hitter.get("team")
    raw_name = hitter.get("name") or ""
    parts = name_parts(raw_name)

    ok = overrides.get(override_key(hitter))
    if ok:
        pid = str(ok.get("playerId"))
        if pid in by_id:
            return by_id[pid], "manual_override", False
        return {"playerId": ok.get("playerId"), "name": ok.get("expectedName"), "currentTeam": norm_team(team)}, "manual_override_id_only", True

    for k in ["playerId", "id", "mlbId", "personId"]:
        v = hitter.get(k)
        if v and str(v) in by_id:
            return by_id[str(v)], "direct_id", False

    candidate, why = choose(by_full.get(parts["full"], []), team)
    if candidate:
        return candidate, f"exact_full_name:{why}", False

    if parts["last"] and parts["suffix"]:
        candidate, why = choose(by_last_suffix.get(f"{parts['last']}|{parts['suffix']}", []), team)
        if candidate:
            suspicious = parts["last"] in DANGEROUS_LAST_NAMES and "team_match" not in why
            return candidate, f"last_suffix:{why}", suspicious

    if parts["last"] and parts["firstInitial"]:
        candidate, why = choose(by_last_initial.get(f"{parts['last']}|{parts['firstInitial']}", []), team)
        if candidate:
            suspicious = "ambiguous" in why
            return candidate, f"last_first_initial:{why}", suspicious

    if parts["last"]:
        candidates = by_last.get(parts["last"], []) or []
        allow = parts["last"] not in DANGEROUS_LAST_NAMES and len(candidates) <= 2
        candidate, why = choose(candidates, team, allow_unsafe=allow)
        if candidate:
            suspicious = allow and "unsafe" in why
            return candidate, f"last_name:{why}", suspicious

    # Fuzzy only when very strong.
    key = parts["full"]
    best, best_score = None, 0
    for row in by_id.values():
        score = SequenceMatcher(None, key, row["nameKey"]).ratio()
        if parts["last"] and parts["last"] == row.get("last"):
            score += .18
        if team and row.get("currentTeam") == norm_team(team):
            score += .06
        if score > best_score:
            best, best_score = row, score
    if best and best_score >= .92:
        return best, f"fuzzy:{best_score:.2f}", True

    return None, "unresolved", False

def main():
    slate_path = DATA / "slate.json"
    if not slate_path.exists():
        slate_path = ROOT / "app" / "slate.json"
    slate = load(slate_path, {"hitters": []})
    overrides = load(DATA / "manual-player-overrides.json", {"overrides": {}}).get("overrides", {})
    people = get_players()
    indexes = build_indexes(people)

    identities = {}
    unresolved = []
    suspicious = []

    for h in slate.get("hitters", []) or []:
        key = f"{h.get('team')}|{h.get('name')}"
        player, method, is_suspicious = resolve(h, indexes, overrides)
        if not player:
            row = {"slateKey": key, "name": h.get("name"), "team": h.get("team"), "method": method, "parts": name_parts(h.get("name"))}
            unresolved.append(row)
            identities[key] = {**row, "resolved": False, "trusted": False}
            continue

        row = {
            "slateKey": key,
            "name": h.get("name"),
            "team": h.get("team"),
            "playerId": player.get("playerId"),
            "resolvedMlbName": player.get("name"),
            "resolvedCurrentTeam": player.get("currentTeam"),
            "position": player.get("primaryPosition"),
            "method": method,
            "suspicious": bool(is_suspicious),
            "trusted": not bool(is_suspicious),
            "resolved": True
        }
        identities[key] = row
        if is_suspicious:
            suspicious.append(row)

    out = {
        "version": "8.0",
        "updatedAt": dt.datetime.now().isoformat(),
        "season": SEASON,
        "totalHitters": len(slate.get("hitters", []) or []),
        "resolvedCount": len([x for x in identities.values() if x.get("resolved")]),
        "trustedCount": len([x for x in identities.values() if x.get("trusted")]),
        "suspiciousCount": len(suspicious),
        "unresolvedCount": len(unresolved),
        "identities": identities,
        "suspicious": suspicious,
        "unresolved": unresolved,
        "rule": "Player stats must be attached by MLBAM playerId. Suspicious and unresolved identities lower confidence."
    }
    save(DATA / "player-identity-map.json", out)
    print(f"Identity map: {out['resolvedCount']} resolved / {out['trustedCount']} trusted / {out['suspiciousCount']} suspicious / {out['unresolvedCount']} unresolved")

if __name__ == "__main__":
    main()
