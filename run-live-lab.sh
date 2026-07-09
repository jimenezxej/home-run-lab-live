#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="python3"
fi
echo "Starting Home Run Lab auto-refresh engine..."
echo "Leave this terminal open while you want live updates."
"$PY" scripts/auto_refresh.py
