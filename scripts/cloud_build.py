#!/usr/bin/env python3
from pathlib import Path
import subprocess

def run(command, required=False):
    path = Path(command[1]) if len(command) > 1 and command[1].endswith(".py") else None
    if path and not path.exists():
        print("SKIP missing:", path)
        return
    print("RUN:", " ".join(command), flush=True)
    result = subprocess.run(command)
    if required and result.returncode:
        raise SystemExit(result.returncode)

run(["python3","scripts/prepare_cloud_data.py"], True)
run(["python3","pipeline.py"], False)
run(["python3","backend/identity/build_player_identity_map.py"], False)
run(["python3","backend/hitters/resolve_slate_hitter_stats.py"], False)
run(["python3","backend/quality/identity_audit.py"], False)
run(["python3","backend/quality/season_stats_audit.py"], False)
run(["python3","backend/quality/protect_season_stats.py"], False)
run(["python3","backend/pitchers/enrich_pitchers.py"], False)
run(["python3","backend/pitchers/build_pitch_zone_profiles.py"], False)
run(["python3","backend/model/scoring.py"], True)
run(["python3","backend/model/intelligence_engine.py"], True)
run(["python3","backend/live/build_game_state.py"], False)
run(["python3","backend/live/filter_live_boards.py"], False)
run(["python3","backend/history/build_hr_history.py","--days","30"], False)
run(["python3","backend/history/audit_hr_history.py"], False)
run(["python3","scripts/build_github_pages.py"], True)
run(["python3","scripts/verify_pages_build.py"], True)
print("Cloud build completed.")
