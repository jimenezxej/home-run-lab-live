# Home Run Lab 8.3 - Safe Live Daily Engine

This fixes the issue where HR tracker updates can cause PA/H/HR to go back to zero.

The fix:
- HR history builder ONLY writes `data/hr-history.json` and `data/hr-history-audit.json`.
- It never touches `data/slate.json`.
- The all-day command always re-attaches verified hitter stats AFTER any slate refresh.
- A guard stops the build if too many PA values are missing.
- Live boards remove players after their game starts.
- HR tracker updates every loop.

## Install

```bash
cd ~
unzip ~/home-run-lab-8.3-safe-live-daily-engine.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-8.3-safe-live-daily-engine/* .

python3 scripts/run_daily_live_once.py
```

## Daily all-in-one command

Run this every morning:

```bash
cd ~/homerun-lab
bash run-daily-live.sh
```

Leave that terminal open.

## Preview command in another terminal

```bash
cd ~/homerun-lab/dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```
