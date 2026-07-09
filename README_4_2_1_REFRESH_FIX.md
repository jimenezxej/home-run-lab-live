# Home Run Lab 4.2.1 Refresh Fix

Fixes the auto-refresh engine so it does not immediately run a second full pipeline refresh after startup.

## Install

```bash
cd ~
unzip ~/home-run-lab-4.2.1-refresh-fix.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.2.1-refresh-fix/* .
python3 scripts/build_github_pages.py
```

## Run

```bash
cd ~/homerun-lab
python3 scripts/auto_refresh.py
```
