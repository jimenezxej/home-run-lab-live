#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="python3"
fi

echo "Home Run Lab 8.3 Daily Live Engine"
echo "Runs the full safe refresh every 5 minutes."
echo "Leave this terminal open."
echo

while true; do
  echo
  echo "===== SAFE LIVE REFRESH $(date) ====="
  $PY scripts/run_daily_live_once.py || echo "Refresh failed. Check output above."
  echo "Next refresh in 5 minutes."
  sleep 300
done
