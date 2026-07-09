#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PORT="${PORT:-8000}"
PY="$ROOT/.venv/bin/python"
LOG_SERVER="$ROOT/server.log"
LOG_HR="$ROOT/hr-tracker.log"

printf '\n==========================================\n THE HOME RUN LAB 3.1\n==========================================\n\n'

[ -f pipeline.py ] || { echo "ERROR: pipeline.py missing"; exit 1; }
[ -f app/index.html ] || { echo "ERROR: app/index.html missing"; exit 1; }

if ! command -v python3 >/dev/null 2>&1; then echo "ERROR: python3 not found"; exit 1; fi
if [ ! -d .venv ]; then
  echo "Creating Python environment..."
  python3 -m venv --system-site-packages .venv
fi

echo "Installing/checking Python requirements..."
"$PY" -m pip install -q --upgrade pip || true
"$PY" -m pip install -q -r requirements.txt

# stop stale local server/tracker processes from older runs
pkill -f "http.server $PORT" >/dev/null 2>&1 || true
pkill -f "backend/live_hr_tracker.py" >/dev/null 2>&1 || true

cleanup(){
  echo; echo "Stopping Home Run Lab services..."
  [ -n "${SERVER_PID:-}" ] && kill "$SERVER_PID" >/dev/null 2>&1 || true
  [ -n "${TRACKER_PID:-}" ] && kill "$TRACKER_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "Starting local web server on port $PORT..."
( cd app && "$PY" -m http.server "$PORT" >"$LOG_SERVER" 2>&1 ) &
SERVER_PID=$!
sleep 1
if ! kill -0 "$SERVER_PID" 2>/dev/null; then echo "Server failed:"; cat "$LOG_SERVER"; exit 1; fi
READY=0
for i in {1..20}; do
  if curl -fsS "http://localhost:$PORT" >/dev/null 2>&1; then READY=1; break; fi
  sleep 1
done
[ "$READY" = "1" ] || { echo "Server did not become ready."; cat "$LOG_SERVER"; exit 1; }

echo "Starting live HR tracker every 2 minutes..."
: > "$LOG_HR"
"$PY" backend/live_hr_tracker.py --loop 2 --include-yesterday > >(tee -a "$LOG_HR") 2>&1 &
TRACKER_PID=$!

if [ "${1:-}" = "--tracker-only" ]; then
  echo "Tracker-only mode. Open http://localhost:$PORT?v=3.1"
  wait "$TRACKER_PID"
  exit 0
fi

if [ "${1:-}" = "--no-pipeline" ]; then
  echo "Skipping slate pipeline. Open http://localhost:$PORT?v=3.1"
  xdg-open "http://localhost:$PORT?v=3.1" >/dev/null 2>&1 || true
  wait "$SERVER_PID"
  exit 0
fi

echo "Building live slate now. First run can take several minutes."
"$PY" pipeline.py

printf '\n==========================================\n APP READY: http://localhost:%s?v=3.1\n Tracker log: tail -f ~/homerun-lab/hr-tracker.log\n==========================================\n\n' "$PORT"
xdg-open "http://localhost:$PORT?v=3.1" >/dev/null 2>&1 || true

# Keep the slate fresh every 15 min, while HR tracker runs every 2 min.
while true; do
  sleep 900
  echo "Refreshing slate..."
  "$PY" pipeline.py || true
done
