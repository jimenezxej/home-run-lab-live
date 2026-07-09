#!/usr/bin/env python3
from pathlib import Path
css = Path("frontend/src/styles.css")
if not css.exists():
    raise SystemExit("Missing frontend/src/styles.css")
text = css.read_text(encoding="utf-8")
addition = """
.na{
  color:#5b6678!important;
  background:#eef2f7!important;
  border-color:#cbd5e1!important;
}
"""
if ".na{" not in text:
    css.write_text(text + "\n" + addition, encoding="utf-8")
    print("Added .na style")
else:
    print(".na style already present")
