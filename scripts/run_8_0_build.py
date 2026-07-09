#!/usr/bin/env python3
import subprocess
cmds = [
    ["python3","backend/identity/build_player_identity_map.py"],
    ["python3","backend/hitters/resolve_slate_hitter_stats.py"],
    ["python3","backend/quality/identity_audit.py"],
    ["python3","backend/quality/season_stats_audit.py"],
    ["python3","scripts/patch_8_0_scoring_guard.py"],
    ["python3","backend/model/scoring.py"],
    ["python3","backend/model/intelligence_engine.py"],
    ["python3","scripts/build_github_pages.py"],
    ["python3","scripts/check_8_0_identity.py"]
]
for c in cmds:
    print("RUN:", " ".join(c))
    subprocess.run(c, check=True)
