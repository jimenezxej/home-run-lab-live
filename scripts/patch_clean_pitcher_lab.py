#!/usr/bin/env python3
from pathlib import Path
p = Path("frontend/src/app.js")
text = p.read_text(encoding="utf-8")
start = text.find("function pitchers(){")
if start == -1:
    raise SystemExit("Could not find function pitchers()")
end_candidates = [text.find(marker, start+1) for marker in ["function windAngle", "function weather", "function momentum"]]
end_candidates = [x for x in end_candidates if x != -1]
if not end_candidates:
    raise SystemExit("Could not find end of pitchers()")
end = min(end_candidates)

new_func = r"""
function pitcherDangerScore(p){
  if(!p || p.dataQuality === "tbd") return null;
  const mapScore = (metric, value) => {
    const g = gradeMetric(metric, value);
    if(g === "elite") return 90;
    if(g === "good") return 75;
    if(g === "avg") return 60;
    if(g === "risk") return 44;
    return 32;
  };
  const parts = [
    mapScore("hr9", p.hr9),
    mapScore("barrelA", p.barrelA),
    mapScore("hardHitA", p.hardHitA),
    mapScore("fb", p.fb),
    mapScore("gb", p.gb)
  ];
  return Math.round(parts.reduce((a,b)=>a+b,0)/parts.length);
}
function dangerText(score){
  if(score === null || score === undefined) return "TBD";
  if(score >= 80) return "Attack";
  if(score >= 68) return "Target";
  if(score >= 55) return "Neutral";
  return "Tough";
}
function mixClean(mix){
  if(!mix || !mix.length) return `<span class="pitcher-empty">Pitch mix not available yet</span>`;
  return `<div class="pitch-mix-clean">${mix.slice(0,5).map(m=>`<span class="pitch-chip">${fmt(m.pitch||m.type)} ${fmt(m.pct||m.percent)}%</span>`).join("")}</div>`;
}
function noteBlock(notes){
  if(!notes || !notes.length) return "";
  return `<div class="pitcher-notes"><details><summary>Data notes / fallbacks</summary><ul>${notes.map(n=>`<li>${n}</li>`).join("")}</ul></details></div>`;
}
function qClass(q){return q==="complete"?"good":q==="partial"?"avg":q==="limited"?"risk":"na"}
function pitchers(){
 const rows=Object.values(pitcherProfiles()).map(p=>({...p,danger:pitcherDangerScore(p)})).sort((a,b)=>num(b.danger,-1)-num(a.danger,-1));
 return `${hero("Pitcher Lab","Clean pitcher danger board. Green target signals mean the pitcher is more attackable for home runs; gray means TBD or unavailable.")}
 <section class="card"><div class="lab-note">Read this tab from a hitter's point of view: high HR/9, high barrel allowed, high hard-hit allowed, high FB%, and low GB% are target signals. TBD pitchers show no fake data.</div></section>
 <section class="pitcher-board" style="margin-top:22px">
 ${rows.map(p=>`<article class="pitcher-card-clean">
   <div class="pitcher-top">
     <div class="pitcher-name-block">
       <strong>${fmt(p.name)}</strong>
       <span>${fmt(p.team)} · ${fmt(p.hand)}HP · <span class="metric-badge ${qClass(p.dataQuality)}"><b>${p.dataQuality}</b><small>Quality</small></span></span>
     </div>
     <div class="pitcher-danger ${gradeClass(gradeMetric("hr_edge",p.danger))}">
       <b>${fmt(p.danger,"N/A")}</b>
       <small>${dangerText(p.danger)}</small>
     </div>
   </div>
   <div class="pitcher-body">
     <div class="pitcher-section-title">Home Run Risk</div>
     <div class="pitcher-metric-grid">
       <div class="pitcher-metric">${badgeMetric("hr9",p.hr9)}<span>HR/9</span></div>
       <div class="pitcher-metric">${badgeMetric("barrelA",p.barrelA,"%")}<span>Barrel Allowed</span></div>
       <div class="pitcher-metric">${badgeMetric("hardHitA",p.hardHitA,"%")}<span>Hard-Hit Allowed</span></div>
       <div class="pitcher-metric">${badgeMetric("fb",p.fb,"%")}<span>Fly Ball Rate</span></div>
     </div>
     <div class="pitcher-section-title">Run Prevention / Batted-Ball Shape</div>
     <div class="pitcher-metric-grid">
       <div class="pitcher-metric">${badgeMetric("gb",p.gb,"%")}<span>Ground Ball Rate</span></div>
       <div class="pitcher-metric">${badgeMetric("xera",p.xera)}<span>xERA</span></div>
       <div class="pitcher-metric">${badgeMetric("fip",p.fip)}<span>FIP</span></div>
       <div class="pitcher-metric">${badgeMetric("siera",p.siera)}<span>SIERA</span></div>
     </div>
     <div class="pitcher-section-title">Pitch Mix</div>
     ${mixClean(p.mix)}
     ${noteBlock(p.notes)}
   </div>
 </article>`).join("")}
 </section>`;
}
"""
text = text[:start] + new_func + "\n" + text[end:]
p.write_text(text, encoding="utf-8")
print("Patched Pitcher Lab layout")
