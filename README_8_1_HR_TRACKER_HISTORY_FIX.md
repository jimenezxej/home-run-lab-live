# Home Run Lab 8.1 - HR Tracker History Fix

Fixes HR Tracker previous-date data.

Run:

```bash
cd ~
unzip ~/home-run-lab-8.1-hr-tracker-history-fix.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-8.1-hr-tracker-history-fix/* .

python3 backend/history/build_hr_history.py --days 30
python3 backend/history/audit_hr_history.py
python3 scripts/patch_hr_tracker_ui.py
python3 scripts/build_github_pages.py
python3 scripts/check_hr_tracker.py
cd dist
python3 -m http.server 8001
```
