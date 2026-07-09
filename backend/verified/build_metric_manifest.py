#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt

DATA = Path("data")
DATA.mkdir(exist_ok=True)

MANIFEST = {
  "version": "5.0",
  "updatedAt": dt.datetime.now().isoformat(),
  "statuses": {
    "verified": "Directly pulled from an accepted source field in the current slate/data files.",
    "calculated": "Calculated from verified or available source fields using a documented formula.",
    "estimated": "Derived fallback. Must be clearly labeled and must not be used as if verified.",
    "missing": "No trustworthy value available. Display N/A."
  },
  "metrics": {
    "hr_edge": {"type": "calculated", "source": "Home Run Lab model"},
    "model_probability": {"type": "calculated", "source": "Home Run Lab model"},
    "stack_score": {"type": "calculated", "source": "Home Run Lab model"},
    "iso": {"type": "verified_or_estimated", "source": "Source ISO if present; otherwise labeled fallback"},
    "xwobacon": {"type": "verified_or_estimated", "source": "Source xwOBAcon if present; otherwise labeled fallback"},
    "pitcher.hr9": {"type": "verified_or_missing", "source": "Pitcher source field only"},
    "pitcher.fb": {"type": "verified_or_missing", "source": "Pitcher source field only"},
    "pitcher.gb": {"type": "verified_or_missing", "source": "Pitcher source field only"},
    "pitcher.fip": {"type": "verified_or_missing", "source": "Pitcher source field only"},
    "pitcher.siera": {"type": "verified_or_missing", "source": "Pitcher source field only"}
  }
}
(DATA / "metric-manifest.json").write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")
print("Wrote data/metric-manifest.json")
