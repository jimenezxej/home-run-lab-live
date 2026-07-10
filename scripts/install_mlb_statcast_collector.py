#!/usr/bin/env python3
from pathlib import Path

def replace_in_file(path: Path) -> None:
    if not path.exists():
        print("SKIP missing:", path)
        return

    text = path.read_text(encoding="utf-8")
    old = "backend/pitchers/collect_verified_pitcher_metrics.py"
    new = "backend/pitchers/collect_mlb_statcast_pitcher_metrics.py"

    if old in text:
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        print("Replaced blocked FanGraphs collector in:", path)
    elif new in text:
        print("Already using MLB/Statcast collector:", path)
    else:
        print("Collector reference not found in:", path)

for candidate in [
    Path("scripts/cloud_refresh.py"),
    Path("scripts/cloud_build.py"),
    Path("scripts/run_verified_pitcher_upgrade.py"),
]:
    replace_in_file(candidate)
