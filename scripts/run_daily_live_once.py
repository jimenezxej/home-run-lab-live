#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

def run(cmd, required=True):
    print("RUN:", " ".join(cmd))
    r = subprocess.run(cmd)
    if required and r.returncode != 0:
        sys.exit(r.returncode)

cmds = [
    (["python3","pipeline.py"], False),
    (["python3","backend/identity/build_player_identity_map.py"], True),
    (["python3","backend/hitters/resolve_slate_hitter_stats.py"], True),
    (["python3","backend/quality/identity_audit.py"], True),
    (["python3","backend/quality/season_stats_audit.py"], True),
    (["python3","backend/quality/protect_season_stats.py"], True),
    (["python3","backend/pitchers/enrich_pitchers.py"], False),
    (["python3","backend/pitchers/build_pitch_zone_profiles.py"], False),
    (["python3","backend/model/scoring.py"], True),
    (["python3","backend/model/intelligence_engine.py"], True),
    (["python3","backend/live/build_game_state.py"], True),
    (["python3","backend/live/filter_live_boards.py"], True),
    (["python3","backend/history/build_hr_history.py","--days","30"], True),
    (["python3","backend/history/audit_hr_history.py"], True),
    (["python3","backend/quality/protect_season_stats.py"], True),
    (["python3","scripts/build_github_pages.py"], True),
]
for cmd, required in cmds:
    if Path(cmd[1]).exists() or cmd[1] == "pipeline.py":
        run(cmd, required)
    else:
        print("SKIP missing:", cmd[1])
print("Daily live build complete.")
