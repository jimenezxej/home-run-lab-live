#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ ! -d .venv ]; then python3 -m venv --system-site-packages .venv; fi
PY="$ROOT/.venv/bin/python"
"$PY" -m pip install -q -r requirements.txt
"$PY" pipeline.py
"$PY" backend/live_hr_tracker.py --include-yesterday
