# Home Run Lab 5.0 — Verified Data Engine

This update is about trust.

It adds:
- Metric provenance metadata
- Verified / Calculated / Estimated / Missing status
- Data audit report
- No fake fallback pitcher stats
- No hidden neutral placeholders for important pitcher fields
- Model scorecards showing component breakdown
- Frontend data badges so users can see whether a value is verified, calculated, estimated, or missing

Important rule:
If a stat is not available from the current source, it shows N/A and lowers confidence.

## Install

```bash
cd ~
unzip ~/home-run-lab-5.0-verified-data-engine.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-5.0-verified-data-engine/* .
python3 backend/verified/build_metric_manifest.py
python3 backend/pitchers/enrich_pitchers.py
python3 backend/quality/truth_audit.py
python3 backend/model/scoring.py
python3 backend/verified/attach_provenance.py
python3 scripts/patch_verified_ui.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```
