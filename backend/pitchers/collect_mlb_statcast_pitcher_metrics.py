#!/usr/bin/env python3
"""
Verified pitcher metrics without FanGraphs scraping.

Sources:
- MLB Stats API: IP, HR, BB, HBP, SO, BF, ER
- Baseball Savant Statcast via pybaseball.statcast_pitcher: bb_type

Calculated:
- HR/9 = 9 * HR / IP
- GB% = ground_ball / BIP
- FB% = (fly_ball + popup) / BIP
- FIP using the published FIP equation and a current-season MLB-wide constant
- SIERA using the MLB glossary formula

No neutral defaults. Unavailable data stays null.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import datetime as dt
import json
import math
import time
import urllib.request

import pandas as pd
from pybaseball import statcast_pitcher, cache

ROOT = Path.cwd()
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

NOW_ET = dt.datetime.now(ZoneInfo("America/New_York"))
SEASON = NOW_ET.year
START_DATE = f"{SEASON}-03-01"
END_DATE = NOW_ET.date().isoformat()

TEAM_IDS_URL = "https://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}"
PERSON_STATS_URL = (
    "https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
    "?stats=season&group=pitching&season={season}&gameType=R"
)
TEAM_STATS_URL = (
    "https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    "?stats=season&group=pitching&season={season}&gameType=R"
)

def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HomeRunLab/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))

def load(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback

def save(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None

def integer(value: Any) -> int:
    parsed = number(value)
    return int(parsed) if parsed is not None else 0

def innings_to_outs(value: Any) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    if not text:
        return 0
    if "." in text:
        whole, fraction = text.split(".", 1)
    else:
        whole, fraction = text, "0"
    try:
        innings = int(whole)
    except ValueError:
        return 0
    extra = 1 if fraction.startswith("1") else 2 if fraction.startswith("2") else 0
    return innings * 3 + extra

def outs_to_innings(outs: int) -> float:
    return outs / 3.0

def profiles_dict(raw: Any) -> dict[str, dict[str, Any]]:
    profiles = raw.get("profiles", raw) if isinstance(raw, dict) else {}
    return profiles if isinstance(profiles, dict) else {}

def player_id(profile: dict[str, Any]) -> int | None:
    candidates = [
        profile.get("playerId"),
        profile.get("id"),
        (profile.get("raw") or {}).get("id"),
        (profile.get("raw") or {}).get("playerId"),
    ]
    for candidate in candidates:
        try:
            if candidate is not None:
                return int(candidate)
        except (TypeError, ValueError):
            pass
    return None

def season_stat_for_person(pid: int) -> dict[str, Any] | None:
    data = fetch_json(PERSON_STATS_URL.format(player_id=pid, season=SEASON))
    groups = data.get("stats", [])
    for group in groups:
        for split in group.get("splits", []):
            stat = split.get("stat")
            if isinstance(stat, dict):
                return stat
    return None

def team_pitching_stat(team_id: int) -> dict[str, Any] | None:
    data = fetch_json(TEAM_STATS_URL.format(team_id=team_id, season=SEASON))
    groups = data.get("stats", [])
    for group in groups:
        for split in group.get("splits", []):
            stat = split.get("stat")
            if isinstance(stat, dict):
                return stat
    return None

def league_totals() -> dict[str, float]:
    teams = fetch_json(TEAM_IDS_URL.format(season=SEASON)).get("teams", [])
    totals = {
        "outs": 0,
        "hr": 0,
        "bb": 0,
        "hbp": 0,
        "so": 0,
        "er": 0,
    }

    for team in teams:
        tid = team.get("id")
        if not tid:
            continue
        stat = team_pitching_stat(int(tid))
        if not stat:
            continue
        totals["outs"] += innings_to_outs(stat.get("inningsPitched"))
        totals["hr"] += integer(stat.get("homeRuns"))
        totals["bb"] += integer(stat.get("baseOnBalls"))
        totals["hbp"] += integer(stat.get("hitBatsmen"))
        totals["so"] += integer(stat.get("strikeOuts"))
        totals["er"] += integer(stat.get("earnedRuns"))
        time.sleep(0.03)

    ip = outs_to_innings(int(totals["outs"]))
    if ip <= 0:
        raise RuntimeError("Unable to calculate MLB-wide innings for FIP constant.")

    league_era = 9.0 * totals["er"] / ip
    fip_without_constant = (
        13.0 * totals["hr"]
        + 3.0 * (totals["bb"] + totals["hbp"])
        - 2.0 * totals["so"]
    ) / ip

    totals["ip"] = ip
    totals["era"] = league_era
    totals["fipConstant"] = league_era - fip_without_constant
    return totals

def statcast_batted_ball_rates(pid: int) -> dict[str, Any]:
    frame = statcast_pitcher(START_DATE, END_DATE, pid)
    if frame is None or frame.empty or "bb_type" not in frame.columns:
        return {
            "gb": None,
            "fb": None,
            "groundBalls": 0,
            "flyBalls": 0,
            "popups": 0,
            "lineDrives": 0,
            "bip": 0,
        }

    types = frame["bb_type"].dropna().astype(str)
    valid = types[types.isin(["ground_ball", "fly_ball", "line_drive", "popup"])]
    counts = valid.value_counts().to_dict()

    ground = int(counts.get("ground_ball", 0))
    flies = int(counts.get("fly_ball", 0))
    popups = int(counts.get("popup", 0))
    liners = int(counts.get("line_drive", 0))
    bip = ground + flies + popups + liners

    if bip <= 0:
        gb = fb = None
    else:
        gb = round(100.0 * ground / bip, 3)
        # Popup is treated as an air ball in the displayed FB% denominator.
        fb = round(100.0 * (flies + popups) / bip, 3)

    return {
        "gb": gb,
        "fb": fb,
        "groundBalls": ground,
        "flyBalls": flies,
        "popups": popups,
        "lineDrives": liners,
        "bip": bip,
    }

def calculate_siera(
    strikeouts: int,
    walks: int,
    batters_faced: int,
    ground_balls: int,
    fly_balls: int,
    popups: int,
) -> float | None:
    if batters_faced <= 0:
        return None

    so_pa = strikeouts / batters_faced
    bb_pa = walks / batters_faced
    net_gb_pa = (ground_balls - fly_balls - popups) / batters_faced

    signed_square = (
        net_gb_pa * net_gb_pa
        if net_gb_pa >= 0
        else -(net_gb_pa * net_gb_pa)
    )

    value = (
        6.145
        - 16.986 * so_pa
        + 11.434 * bb_pa
        - 1.858 * net_gb_pa
        + 7.653 * (so_pa ** 2)
        + 6.664 * signed_square
        + 10.130 * so_pa * net_gb_pa
        - 5.195 * bb_pa * net_gb_pa
    )
    return round(value, 3)

def main() -> None:
    cache.enable()

    path = DATA / "pitcher-profiles.json"
    raw = load(path, {"profiles": {}})
    profiles = profiles_dict(raw)

    if not profiles:
        raise SystemExit("No profiles found in data/pitcher-profiles.json")

    print("Calculating current-season MLB FIP constant...")
    league = league_totals()
    fip_constant = league["fipConstant"]
    print(f"MLB FIP constant: {fip_constant:.4f}")

    complete = 0
    unresolved: list[dict[str, Any]] = []
    updated_profiles: dict[str, dict[str, Any]] = {}

    for team, original in profiles.items():
        profile = dict(original)
        pid = player_id(profile)
        name = profile.get("name")

        if pid is None:
            unresolved.append({"team": team, "name": name, "reason": "missing_mlbam_id"})
            updated_profiles[team] = profile
            continue

        print(f"Collecting {team} {name} ({pid})...")
        try:
            official = season_stat_for_person(pid)
            batted = statcast_batted_ball_rates(pid)
        except Exception as exc:
            unresolved.append({
                "team": team,
                "name": name,
                "playerId": pid,
                "reason": str(exc),
            })
            updated_profiles[team] = profile
            continue

        if not official:
            unresolved.append({
                "team": team,
                "name": name,
                "playerId": pid,
                "reason": "no_official_season_pitching_split",
            })
            updated_profiles[team] = profile
            continue

        outs = innings_to_outs(official.get("inningsPitched"))
        ip = outs_to_innings(outs)
        hr = integer(official.get("homeRuns"))
        bb = integer(official.get("baseOnBalls"))
        hbp = integer(official.get("hitBatsmen"))
        so = integer(official.get("strikeOuts"))
        bf = integer(official.get("battersFaced"))
        er = integer(official.get("earnedRuns"))

        hr9 = round(9.0 * hr / ip, 3) if ip > 0 else None
        fip = (
            round(
                (
                    13.0 * hr
                    + 3.0 * (bb + hbp)
                    - 2.0 * so
                ) / ip + fip_constant,
                3,
            )
            if ip > 0
            else None
        )

        siera = calculate_siera(
            strikeouts=so,
            walks=bb,
            batters_faced=bf,
            ground_balls=batted["groundBalls"],
            fly_balls=batted["flyBalls"],
            popups=batted["popups"],
        )

        values = {
            "hr9": hr9,
            "fb": batted["fb"],
            "gb": batted["gb"],
            "fip": fip,
            "siera": siera,
            "ip": round(ip, 3),
            "hrAllowed": hr,
            "walksAllowed": bb,
            "hitBatters": hbp,
            "strikeouts": so,
            "battersFaced": bf,
            "earnedRuns": er,
        }

        provenance = dict(profile.get("provenance") or {})
        now = dt.datetime.now(dt.timezone.utc).isoformat()

        official_fields = {
            "hr9", "fip", "ip", "hrAllowed", "walksAllowed",
            "hitBatters", "strikeouts", "battersFaced", "earnedRuns",
        }

        for field, value in values.items():
            if field in official_fields:
                source = "MLB Stats API season pitching totals"
            elif field in {"fb", "gb"}:
                source = "Baseball Savant Statcast bb_type"
            else:
                source = "Calculated from MLB Stats API and Baseball Savant"

            provenance[field] = {
                "status": "verified" if value is not None else "missing",
                "source": source if value is not None else None,
                "season": SEASON,
                "updatedAt": now,
                "playerId": pid,
            }

        provenance["fip"]["formula"] = (
            "((13*HR)+(3*(BB+HBP))-(2*SO))/IP + current MLB FIP constant"
        )
        provenance["fip"]["fipConstant"] = round(fip_constant, 6)
        provenance["gb"]["formula"] = "ground_ball / Statcast BIP"
        provenance["fb"]["formula"] = "(fly_ball + popup) / Statcast BIP"
        provenance["siera"]["formulaSource"] = "MLB Advanced Stats glossary SIERA formula"

        profile.update(values)
        profile["provenance"] = provenance
        profile["verifiedPitcherMetricsSource"] = (
            "MLB Stats API + Baseball Savant Statcast"
        )
        profile["verifiedPitcherMetricsSeason"] = SEASON
        profile["verifiedPitcherMetricsUpdatedAt"] = now
        profile["battedBallCounts"] = {
            "groundBalls": batted["groundBalls"],
            "flyBalls": batted["flyBalls"],
            "popups": batted["popups"],
            "lineDrives": batted["lineDrives"],
            "bip": batted["bip"],
        }

        required = ["hr9", "fb", "gb", "fip", "siera"]
        missing = [field for field in required if profile.get(field) is None]
        profile["missingFields"] = missing
        profile["realFields"] = sorted(
            set(profile.get("realFields") or [])
            | {field for field in values if profile.get(field) is not None}
        )
        profile["dataQuality"] = "complete" if not missing else "partial"

        if not missing:
            complete += 1

        updated_profiles[team] = profile
        time.sleep(0.05)

    output = {
        "version": "mlb-statcast-pitcher-metrics-1.0",
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "season": SEASON,
        "source": "MLB Stats API + Baseball Savant Statcast",
        "integrityRule": "Missing values remain null. No neutral defaults.",
        "fipConstant": round(fip_constant, 6),
        "leagueTotals": league,
        "completeRequiredProfiles": complete,
        "unresolvedProfiles": unresolved,
        "profiles": updated_profiles,
    }

    save(path, output)
    save(DATA / "verified-pitcher-metrics-audit.json", {
        "version": output["version"],
        "season": SEASON,
        "source": output["source"],
        "fipConstant": output["fipConstant"],
        "totalProfiles": len(profiles),
        "completeRequiredProfiles": complete,
        "unresolvedProfiles": unresolved,
        "requiredMetrics": ["hr9", "fb", "gb", "fip", "siera"],
    })

    print(
        f"Verified pitcher metrics complete: "
        f"{complete}/{len(profiles)} have HR/9, FB%, GB%, FIP and SIERA."
    )
    if unresolved:
        print("Unresolved profiles:")
        for row in unresolved:
            print(" ", row)

if __name__ == "__main__":
    main()
