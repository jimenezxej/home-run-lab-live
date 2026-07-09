#!/usr/bin/env python3
from pathlib import Path

p=Path("frontend/src/app.js")
text=p.read_text(encoding="utf-8")
text=text.replace("<th>Sample</th><th>Reliability</th>", "<th>Sample</th><th>H/HR</th><th>Reliability</th>")
text=text.replace('${fmt(pr.sampleSize,"N/A")} PA<br><span class="sample-bucket ${fmt(pr.sampleBucket,"na")}">${fmt(pr.sampleBucket,"N/A")}</span></td><td>${badgeMetric("confidence",p.scores?.sample_reliability)}</td>',
                  '${fmt(pr.sampleSize,"N/A")} PA<br><span class="sample-bucket ${fmt(pr.sampleBucket,"na")}">${fmt(pr.sampleBucket,"N/A")}</span></td><td>${fmt(pr.seasonHits,"N/A")} H<br>${fmt(pr.seasonHR,"N/A")} HR</td><td>${badgeMetric("confidence",p.scores?.sample_reliability)}</td>')
p.write_text(text, encoding="utf-8")
print("Patched season stats UI")
