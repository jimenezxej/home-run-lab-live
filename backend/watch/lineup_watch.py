#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt, subprocess, time, argparse

ROOT = Path.cwd()
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

def py():
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else "python3"

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

def run(cmd, label):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {label}...")
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
        print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] OK {label}")
        return True
    except Exception as e:
        print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] ERROR {label}: {e}")
        return False

def snapshot():
    slate = load(DATA / "slate.json", None) or load(ROOT / "app" / "slate.json", {})
    games = slate.get("games", []) or []
    pitchers = slate.get("pitchers", {}) or {}
    snap = {
        "date": slate.get("date"),
        "generatedAt": slate.get("generatedAt"),
        "games": len(games),
        "lineups": {},
        "pitchers": {}
    }
    for g in games:
        for side in ["away", "home"]:
            team = g.get(side)
            if not team:
                continue
            status = (g.get("lineupStatus") or {}).get(team) or (g.get("lineupStatus") or {}).get(side) or "projected"
            snap["lineups"][team] = status
            p = pitchers.get(team, {}) or {}
            snap["pitchers"][team] = p.get("name") or "TBD"
    return snap

def diff(old, new):
    changes = []
    if not old:
        return ["initial_snapshot"]
    for team, status in new.get("lineups", {}).items():
        if old.get("lineups", {}).get(team) != status:
            changes.append(f"lineup:{team}:{old.get('lineups',{}).get(team)}->{status}")
    for team, pitcher in new.get("pitchers", {}).items():
        if old.get("pitchers", {}).get(team) != pitcher:
            changes.append(f"pitcher:{team}:{old.get('pitchers',{}).get(team)}->{pitcher}")
    return changes

def rebuild(reason):
    ok = True
    ok = run([py(), "pipeline.py"], "refresh slate / lineups / probable pitchers") and ok
    # Copy app data into data if pipeline writes app/
    app = ROOT / "app"
    for name in ["slate.json", "hr-history.json", "live-events.json"]:
        src = app / name
        if src.exists():
            (DATA / name).write_bytes(src.read_bytes())
    for cmd, label in [
        ([py(), "backend/pitchers/enrich_pitchers.py"], "verified pitcher profiles"),
        ([py(), "backend/pitchers/build_pitch_zone_profiles.py"], "pitch zone profiles"),
        ([py(), "backend/quality/truth_audit.py"], "truth audit"),
        ([py(), "backend/model/scoring.py"], "scoring"),
        ([py(), "backend/verified/attach_provenance.py"], "provenance summary"),
        ([py(), "scripts/build_github_pages.py"], "frontend build"),
    ]:
        if Path(cmd[1]).exists():
            ok = run(cmd, label) and ok
    return ok

def write_status(snap, changes, ok):
    lineups = snap.get("lineups", {})
    confirmed = len([x for x in lineups.values() if str(x).lower() == "confirmed"])
    total = len(lineups)
    pitchers = snap.get("pitchers", {})
    missing_pitchers = [t for t,p in pitchers.items() if not p or p == "TBD"]
    save(DATA / "update-status.json", {
        "version": "5.2",
        "updatedAt": dt.datetime.now().isoformat(),
        "lastRefreshOk": ok,
        "changes": changes,
        "games": snap.get("games", 0),
        "lineupsConfirmed": confirmed,
        "lineupsTotal": total,
        "lineups": lineups,
        "missingProbablePitchers": missing_pitchers,
        "pitchers": pitchers,
        "message": "Watching lineup confirmations and pitcher changes."
    })

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=300, help="seconds between checks; default 300")
    args = ap.parse_args()

    old = load(DATA / "lineup-snapshot.json", None)

    while True:
        ok = rebuild("lineup watch")
        new = snapshot()
        changes = diff(old, new)
        save(DATA / "lineup-snapshot.json", new)
        write_status(new, changes, ok)
        old = new
        print(f"Lineup watch: {len(changes)} changes; next check in {args.interval}s")
        if args.once:
            break
        time.sleep(max(60, args.interval))

if __name__ == "__main__":
    main()
