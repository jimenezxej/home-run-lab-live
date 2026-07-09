#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import subprocess, json, time, datetime as dt, urllib.request
from typing import Any, Dict, List

ROOT = Path.cwd()
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

LIVE_TRACKER_INTERVAL = 120
PIPELINE_INTERVAL = 600
SLEEP_SECONDS = 10

MLB_SCHEDULE = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=linescore,status"
LIVE_STATES = {"In Progress","Manager challenge","Umpire Review","Warmup","Delayed","Delayed Start","Suspended"}

def now_iso() -> str:
    return dt.datetime.now().isoformat()

def log(msg: str):
    line = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with (ROOT / "auto-refresh.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def run(cmd: List[str], label: str) -> bool:
    log(f"START {label}: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
        log(f"OK {label}")
        return True
    except Exception as e:
        log(f"ERROR {label}: {e}")
        return False

def py() -> str:
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else "python3"

def fetch_json(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def today_str() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")

def current_slate_date() -> str | None:
    for p in [DATA / "slate.json", ROOT / "app" / "slate.json", ROOT / "slate.json"]:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")).get("date")
            except Exception:
                pass
    return None

def games_live_on(date_s: str) -> bool:
    try:
        data = fetch_json(MLB_SCHEDULE.format(date=date_s))
        for d in data.get("dates", []):
            for g in d.get("games", []):
                detailed = g.get("status", {}).get("detailedState")
                abstract = g.get("status", {}).get("abstractGameState")
                if detailed in LIVE_STATES or abstract == "Live":
                    return True
    except Exception as e:
        log(f"Could not check live games for {date_s}: {e}")
        return True
    return False

def should_force_new_day() -> bool:
    cur = current_slate_date()
    if not cur or cur == today_str():
        return False
    if games_live_on(cur):
        log(f"Slate date {cur} still has live games; holding rollover.")
        return False
    return True

def write_health(extra: Dict[str, Any]):
    path = DATA / "health.json"
    health = {}
    if path.exists():
        try: health = json.loads(path.read_text(encoding="utf-8"))
        except Exception: health = {}
    health.update(extra)
    health["updatedAt"] = now_iso()
    path.write_text(json.dumps(health, indent=2), encoding="utf-8")

def copy_app_data_to_data():
    app = ROOT / "app"
    for name in ["slate.json","hr-history.json","live-events.json"]:
        src = app / name
        if src.exists():
            (DATA / name).write_bytes(src.read_bytes())

def full_refresh(reason: str):
    log(f"FULL REFRESH: {reason}")
    run([py(), "pipeline.py"], "pipeline")
    copy_app_data_to_data()
    run([py(), "backend/model/scoring.py"], "scoring")
    run([py(), "backend/quality/pitcher_audit.py"], "pitcher audit")
    run([py(), "scripts/build_github_pages.py"], "build frontend")
    write_health({"lastFullRefresh": now_iso(), "lastFullRefreshReason": reason, "currentSlateDate": current_slate_date()})

def live_refresh():
    run([py(), "backend/tracker/live_hr_tracker.py"], "live HR tracker")
    run([py(), "scripts/build_github_pages.py"], "build frontend after live tracker")
    write_health({"lastLiveRefresh": now_iso()})

def main():
    log("Home Run Lab 4.2.1 Auto Refresh Engine started")
    full_refresh("startup")

    # Fix: timers start AFTER startup refresh completes, preventing immediate duplicate pipeline runs.
    last_live = time.time()
    last_pipeline = time.time()

    while True:
        t = time.time()
        if t - last_live >= LIVE_TRACKER_INTERVAL:
            live_refresh()
            last_live = t
        if t - last_pipeline >= PIPELINE_INTERVAL:
            full_refresh("midnight rollover" if should_force_new_day() else "scheduled lineup/pitcher/slate refresh")
            last_pipeline = t
        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Auto Refresh Engine stopped by user")
