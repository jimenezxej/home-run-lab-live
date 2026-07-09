# Home Run Lab 5.2 — Lineup Watch Engine

Adds:
- Automatic lineup/probable-pitcher refresh loop
- Rebuilds pitcher profiles, pitch-zone profiles, scoring, and frontend after updates
- Writes `data/update-status.json`
- Tracks confirmed/projected/TBD lineup states
- Keeps the app current during the day

## Install

```bash
cd ~
unzip ~/home-run-lab-5.2-lineup-watch-engine.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-5.2-lineup-watch-engine/* .
python3 scripts/build_github_pages.py
```

## Morning daily workflow

Use this as your main all-day command:

```bash
cd ~/homerun-lab
bash run-live-day.sh
```

Leave it open.

In a second terminal:

```bash
cd ~/homerun-lab/dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```
