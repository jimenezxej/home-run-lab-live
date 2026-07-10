#!/usr/bin/env python3
from pathlib import Path
from zoneinfo import ZoneInfo
import datetime as dt
import json
import shutil
import subprocess

ROOT = Path.cwd()
TODAY_ET = dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()

def run(cmd, required=True):
    print("RUN:", " ".join(cmd), flush=True)
    result = subprocess.run(cmd)
    if required and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.returncode

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def slate_date(obj):
    if not isinstance(obj, dict):
        return None
    return (
        obj.get("date")
        or obj.get("slateDate")
        or obj.get("gameDate")
        or obj.get("generatedFor")
    )

def find_fresh_slate():
    candidates = [
        ROOT / "app" / "slate.json",
        ROOT / "data" / "slate.json",
        ROOT / "slate.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        obj = load_json(path)
        date_value = slate_date(obj)
        print(f"SLATE CANDIDATE: {path} date={date_value}")
        if date_value == TODAY_ET:
            return path
    raise SystemExit(
        f"REFUSING TO DEPLOY STALE SLATE: no slate.json is dated {TODAY_ET}"
    )

def sync_slate(source):
    targets = [
        ROOT / "data" / "slate.json",
        ROOT / "app" / "slate.json",
        ROOT / "slate.json",
    ]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() != source.resolve():
            shutil.copy2(source, target)
        print("SYNCED:", target)

def main():
    print("Eastern slate date:", TODAY_ET)

    run(["python3", "pipeline.py", "--date", TODAY_ET, "--quick"], required=True)

    source = find_fresh_slate()
    sync_slate(source)

    run(["python3", "backend/identity/build_player_identity_map.py"])
    run(["python3", "backend/hitters/resolve_slate_hitter_stats.py"])
    run(["python3", "backend/quality/identity_audit.py"])
    run(["python3", "backend/quality/season_stats_audit.py"])
    run(["python3", "backend/quality/protect_season_stats.py"])

    run(["python3", "backend/pitchers/enrich_pitchers.py"], required=False)
    run(["python3", "backend/pitchers/build_pitch_zone_profiles.py"], required=False)
    run(["python3", "backend/pitchers/collect_verified_pitcher_metrics.py"])
    run(["python3", "backend/model/scoring.py"])
    run(["python3", "backend/model/intelligence_engine.py"])
    run(["python3", "backend/model/apply_verified_pitcher_reasons.py"])

    run(["python3", "backend/live/build_game_state.py"])
    run(["python3", "backend/live/filter_live_boards.py"])
    run(["python3", "backend/history/build_hr_history.py", "--days", "30"])
    run(["python3", "backend/history/audit_hr_history.py"])

    run(["python3", "scripts/build_github_pages.py"])
    run(["python3", "scripts/verify_pages_build.py"])

    dist_slate = load_json(ROOT / "dist" / "slate.json")
    deployed_date = slate_date(dist_slate)
    if deployed_date != TODAY_ET:
        raise SystemExit(
            f"REFUSING TO DEPLOY: dist/slate.json date={deployed_date}, expected={TODAY_ET}"
        )

    print(f"AUTOMATIC REFRESH PASSED FOR {TODAY_ET}")

if __name__ == "__main__":
    main()
