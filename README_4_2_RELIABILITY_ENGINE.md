# Home Run Lab 4.2 Reliability Engine

This upgrade focuses on the data side:

- Pitcher completeness audit
- Better pitcher fallback handling
- Automatic slate rollover after midnight
- Does not roll to tomorrow while games are still live
- Runs live HR tracker every 2 minutes
- Runs lineup / pitcher / slate refresh every 10 minutes
- Rebuilds scores and frontend output after each refresh
- Writes health/status files so the app can show when data is stale

## Install

```bash
cd ~
unzip ~/home-run-lab-4.2-reliability-engine.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.2-reliability-engine/* .
python3 backend/quality/pitcher_audit.py
python3 scripts/build_github_pages.py
```

## Run the auto-refresh engine

Use this instead of manually running pipeline over and over:

```bash
cd ~/homerun-lab
python3 scripts/auto_refresh.py
```

Leave that terminal open while you want the app to stay live.

Then in a second terminal:

```bash
cd ~/homerun-lab/dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```

## Files this creates

- `data/health.json`
- `data/pitcher-audit.json`
- `data/update-log.json`
- updated `data/scores.json`
- rebuilt `dist/`
