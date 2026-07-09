#!/usr/bin/env python3
from pathlib import Path

p = Path("frontend/src/app.js")
text = p.read_text(encoding="utf-8")

text = text.replace("<th>Stack</th><th>KHR</th>", "<th>Stack</th><th>Sample</th><th>Reliability</th><th>KHR</th>")

old = '<td>${badgeMetric("stack",p.scores?.stack_score)}</td>\n <td>${badgeMetric("khr",pr.khr)}</td>'
new = '<td>${badgeMetric("stack",p.scores?.stack_score)}</td><td>${fmt(pr.sampleSize,"N/A")} PA<br><span class="sample-bucket ${fmt(pr.sampleBucket,"na")}">${fmt(pr.sampleBucket,"N/A")}</span></td><td>${badgeMetric("confidence",p.scores?.sample_reliability)}</td>\n <td>${badgeMetric("khr",pr.khr)}</td>'
text = text.replace(old, new)

text = text.replace(
    "<li>Stack score: ${fmt(p.scores?.stack_score)}</li>",
    "<li>Stack score: ${fmt(p.scores?.stack_score)}</li><li>Sample: ${fmt(p.profile?.sampleSize, \'N/A\')} PA · reliability ${fmt(p.scores?.sample_reliability, \'N/A\')}</li><li>Raw HR Edge before sample shrinkage: ${fmt(p.scores?.raw_hr_edge, \'N/A\')}</li><li>Sample-adjusted edge: ${fmt(p.scores?.sample_adjusted_edge, \'N/A\')}</li>"
)

p.write_text(text, encoding="utf-8")

css = Path("frontend/src/styles.css")
c = css.read_text(encoding="utf-8")
addition = '''
.sample-bucket{display:inline-block;margin-top:4px;border-radius:999px;padding:3px 7px;font-size:10px;font-weight:950;text-transform:uppercase;background:#f1f5f9;color:#475569;border:1px solid #cbd5e1;}
.sample-bucket.tiny,.sample-bucket.small{background:#fee2e2;color:#991b1b;border-color:#ef4444;}
.sample-bucket.thin{background:#ffedd5;color:#9a3412;border-color:#f97316;}
.sample-bucket.moderate{background:#fef3c7;color:#854d0e;border-color:#f59e0b;}
.sample-bucket.solid,.sample-bucket.strong{background:#d1fae5;color:#047857;border-color:#10b981;}
'''
if ".sample-bucket" not in c:
    css.write_text(c + "\n" + addition, encoding="utf-8")
print("Patched sample size UI")
