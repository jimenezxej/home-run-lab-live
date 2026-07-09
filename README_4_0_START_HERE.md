# Home Run Lab 4.0 Starter Kit

This kit upgrades the project from a flat GitHub Pages upload into a cleaner app structure.

## Install into your Chromebook repo

```bash
cd ~/homerun-lab
cp -r ~/home-run-lab-4.0-starter-kit/* .
python3 scripts/upgrade_repo_to_4_0.py
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
python3 scripts/check_project.py
```

Preview:

```bash
cd ~/homerun-lab/dist
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000
```
