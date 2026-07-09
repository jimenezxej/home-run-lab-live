#!/usr/bin/env python3
from pathlib import Path
p=Path("frontend/src/styles.css")
text=p.read_text(encoding="utf-8")
addition = r"""
.metric-badge{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  flex-direction:column;
  min-width:58px;
  min-height:42px;
  border-radius:12px;
  border:1px solid currentColor;
  padding:4px 8px;
  font-weight:950;
  line-height:1.05;
}
.metric-badge b{font-size:14px;}
.metric-badge small{font-size:9px;text-transform:uppercase;letter-spacing:.08em;opacity:.8;margin-top:3px;}
.metric-badge.elite,.legend.elite,.dot.elite{color:#047857;background:#d1fae5;border-color:#10b981;}
.metric-badge.good,.legend.good,.dot.good{color:#166534;background:#dcfce7;border-color:#22c55e;}
.metric-badge.avg,.legend.avg,.dot.avg{color:#854d0e;background:#fef3c7;border-color:#f59e0b;}
.metric-badge.risk,.legend.risk,.dot.risk{color:#9a3412;background:#ffedd5;border-color:#f97316;}
.metric-badge.poor,.legend.poor,.dot.poor{color:#991b1b;background:#fee2e2;border-color:#ef4444;}
.metric-badge.na,.legend.na,.dot.na{color:#475569;background:#f1f5f9;border-color:#cbd5e1;}
.guide-strip{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin:0 0 22px;}
.legend{border:1px solid currentColor;border-radius:999px;padding:9px 13px;font-weight:950;font-size:13px;}
.factor-dots{display:flex;gap:5px;justify-content:center;}
.dot{display:inline-block;width:14px;height:14px;border-radius:999px;border:1px solid currentColor;}
.guide-row{border:1px solid var(--line);border-radius:16px;padding:14px;margin-bottom:12px;background:#fff;}
.guide-row strong{color:var(--navy);font-size:17px;}
.guide-row p{margin:6px 0 0;color:var(--muted);line-height:1.45;}
"""
if ".metric-badge{" not in text:
    p.write_text(text + "\n" + addition, encoding="utf-8")
    print("Added color guide CSS")
else:
    print("Color guide CSS already present")
