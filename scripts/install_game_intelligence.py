#!/usr/bin/env python3
from pathlib import Path
def patch(path,anchor,line):
    if not path.exists():
        print("SKIP",path);return
    t=path.read_text(encoding="utf-8")
    if line.strip() in t:
        print("Already patched",path);return
    if anchor not in t:
        print("Anchor not found",path);return
    path.write_text(t.replace(anchor,anchor+"\n"+line,1),encoding="utf-8")
    print("Patched",path)

patch(Path("scripts/cloud_refresh.py"),
'    run(["python3", "backend/model/apply_verified_pitcher_reasons.py"])',
'    run(["python3", "backend/model/build_game_dashboard.py"])')

patch(Path("scripts/cloud_build.py"),
'run(["python3", "backend/model/apply_verified_pitcher_reasons.py"], required=True)',
'run(["python3", "backend/model/build_game_dashboard.py"], required=True)')

patch(Path("scripts/run_daily_live_once.py"),
'run(["python3", "backend/model/intelligence_engine.py"])',
'run(["python3", "backend/model/build_game_dashboard.py"])')
