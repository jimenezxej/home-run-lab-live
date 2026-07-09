#!/usr/bin/env python3
from pathlib import Path
p = Path("frontend/src/styles.css")
text = p.read_text(encoding="utf-8")
addition = """
/* Clean Pitcher Lab 4.6.1 */
.pitcher-board{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:22px;align-items:start;}
.pitcher-card-clean{background:#fff;border:1px solid var(--line);border-radius:24px;box-shadow:var(--shadow);overflow:hidden;}
.pitcher-top{display:flex;justify-content:space-between;gap:18px;padding:22px 22px 18px;background:linear-gradient(135deg,#fff,#f6f9fd);border-bottom:1px solid var(--line);}
.pitcher-name-block strong{display:block;color:var(--navy);font-size:25px;line-height:1.05;letter-spacing:-.04em;}
.pitcher-name-block span{display:block;color:var(--muted);margin-top:6px;font-weight:800;}
.pitcher-danger{min-width:92px;min-height:76px;border-radius:20px;display:flex;flex-direction:column;justify-content:center;align-items:center;border:1px solid currentColor;font-weight:950;}
.pitcher-danger b{font-size:30px;line-height:1;}
.pitcher-danger small{margin-top:5px;font-size:10px;text-transform:uppercase;letter-spacing:.1em;}
.pitcher-body{padding:18px 22px 22px;}
.pitcher-section-title{color:var(--navy);font-size:13px;letter-spacing:.13em;text-transform:uppercase;font-weight:950;margin:4px 0 10px;}
.pitcher-metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px;}
.pitcher-metric{background:#f8fbff;border:1px solid var(--line);border-radius:16px;padding:12px 8px;text-align:center;}
.pitcher-metric .metric-badge{margin:0 auto 7px;}
.pitcher-metric span{display:block;color:var(--muted);font-size:11px;line-height:1.2;font-weight:900;text-transform:uppercase;}
.pitch-mix-clean{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;}
.pitch-chip{background:var(--navy);color:#fff;border-radius:999px;padding:8px 11px;font-weight:900;font-size:12px;}
.pitcher-notes{border-top:1px solid var(--line);padding-top:14px;margin-top:4px;}
.pitcher-notes details{background:#f8fbff;border:1px solid var(--line);border-radius:14px;padding:11px 13px;}
.pitcher-notes summary{cursor:pointer;color:var(--navy);font-weight:950;font-size:13px;}
.pitcher-notes ul{margin:10px 0 0;padding-left:18px;color:var(--muted);font-size:13px;line-height:1.45;}
.pitcher-empty{color:var(--muted);font-size:13px;font-weight:800;}
@media(max-width:680px){.pitcher-board{grid-template-columns:1fr;}.pitcher-top{display:block;text-align:center;}.pitcher-danger{margin:14px auto 0;}.pitcher-metric-grid{grid-template-columns:repeat(2,1fr);}}
"""
if ".pitcher-board" not in text:
    p.write_text(text + "\n" + addition, encoding="utf-8")
    print("Added clean pitcher lab CSS")
else:
    print("Clean pitcher lab CSS already present")
