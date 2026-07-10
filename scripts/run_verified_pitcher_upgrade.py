#!/usr/bin/env python3
import subprocess,sys
cmds=[
 ["python3","backend/pitchers/collect_mlb_statcast_pitcher_metrics.py"],
 ["python3","backend/quality/audit_verified_pitcher_metrics.py"],
 ["python3","backend/model/scoring.py"],
 ["python3","backend/model/intelligence_engine.py"],
 ["python3","backend/model/apply_verified_pitcher_reasons.py"],
 ["python3","scripts/build_github_pages.py"],
]
for c in cmds:
 print("RUN:"," ".join(c),flush=True)
 if subprocess.run(c).returncode:sys.exit(1)
print("Verified pitcher metrics upgrade complete.")
