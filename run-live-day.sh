#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PY=".venv/bin/python"
if [ ! -x "$PY" ]; then PY="python3"; fi
echo "Home Run Lab Live Day Runner"
echo "Watches lineups, pitchers, scores, and verified HR history. Leave this terminal open all day."
$PY backend/verified/build_metric_manifest.py || true
$PY backend/history/build_hr_history.py --days 30 || true
$PY backend/history/audit_hr_history.py || true
$PY backend/pitchers/enrich_pitchers.py || true
$PY backend/pitchers/build_pitch_zone_profiles.py || true
$PY backend/quality/truth_audit.py || true
$PY backend/model/scoring.py || true
$PY backend/verified/attach_provenance.py || true
$PY scripts/patch_weather_glossary.py || true
$PY scripts/build_github_pages.py || true
if [ -f backend/watch/lineup_watch.py ]; then
  $PY backend/watch/lineup_watch.py --interval 300
elif [ -f scripts/auto_refresh.py ]; then
  $PY scripts/auto_refresh.py
else
  echo "No watcher found. Running simple 10-minute loop."
  while true; do
    $PY pipeline.py || true
    $PY backend/history/build_hr_history.py --days 30 || true
    $PY backend/pitchers/enrich_pitchers.py || true
    $PY backend/pitchers/build_pitch_zone_profiles.py || true
    $PY backend/model/scoring.py || true
    $PY scripts/build_github_pages.py || true
    sleep 600
  done
fi
