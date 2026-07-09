#!/usr/bin/env python3
from pathlib import Path

app = Path("frontend/src/app.js")
text = app.read_text(encoding="utf-8")

text = text.replace("pitcherProfiles:null, glossary:null", "pitcherProfiles:null, pitchZones:null, glossary:null")

if 'pitch-zone-profiles.json' not in text:
    text = text.replace(
        'state.pitcherProfiles=await loadJSON("pitcher-profiles.json",{profiles:{}});',
        'state.pitcherProfiles=await loadJSON("pitcher-profiles.json",{profiles:{}});\n  state.pitchZones=await loadJSON("pitch-zone-profiles.json",{profiles:{}});'
    )

helper = '''
function pitchZoneFor(team){
  return state.pitchZones?.profiles?.[team] || null;
}
function zoneCell(v){
  const n = Number(v)||0;
  const cls = n>=75 ? "zone-hot" : n>=45 ? "zone-mid" : n>0 ? "zone-cool" : "zone-empty";
  return `<div class="zone-cell ${cls}"><span>${n ? n : ""}</span></div>`;
}
function pitchZoneCard(team){
  const z = pitchZoneFor(team);
  if(!z) return "";
  const status = z.status === "verified_mix" ? "Pitch mix available" : z.status === "missing" ? "Missing" : "Profile placeholder";
  const tag = z.status === "verified_mix" ? "verified" : z.status === "missing" ? "missing" : "estimated";
  return `<div class="zone-card">
    <div class="zone-head">
      <strong>Strike Zone Visual</strong>
      <span class="status-tag ${tag}">${status}</span>
    </div>
    <div class="zone-grid">
      ${(z.zoneGrid||[]).map(zoneCell).join("")}
    </div>
    <div class="pitch-frequency">
      ${(z.mix||[]).map(m=>`<span class="pitch-chip">${fmt(m.pitch)} ${fmt(m.pct)}%</span>`).join("") || `<span class="pitcher-empty">No pitch mix yet</span>`}
    </div>
    <div class="zone-note">${(z.notes||[]).slice(0,2).join(" ")}</div>
  </div>`;
}
'''
if "function pitchZoneFor(" not in text:
    idx = text.find("function pitchers(){")
    if idx != -1:
        text = text[:idx] + helper + "\n" + text[idx:]
    else:
        text += "\n" + helper

if "${pitchZoneCard(p.team)}" not in text:
    text = text.replace("${mixClean(p.mix)}", "${mixClean(p.mix)}\n     ${pitchZoneCard(p.team)}")

app.write_text(text, encoding="utf-8")

css = Path("frontend/src/styles.css")
c = css.read_text(encoding="utf-8")
addition = '''
/* Pitch Zone Visuals 5.1 */
.zone-card{margin-top:14px;border:1px solid var(--line);border-radius:18px;background:#f8fbff;padding:14px;}
.zone-head{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px;}
.zone-head strong{color:var(--navy);font-size:14px;text-transform:uppercase;letter-spacing:.08em;}
.zone-grid{width:210px;max-width:100%;aspect-ratio:1/1.28;margin:0 auto 12px;display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,1fr);border:3px solid var(--navy);background:#fff;}
.zone-cell{border:1px solid #cbd5e1;display:flex;align-items:center;justify-content:center;font-weight:950;font-size:13px;}
.zone-hot{background:#fee2e2;color:#991b1b;}
.zone-mid{background:#ffedd5;color:#9a3412;}
.zone-cool{background:#dbeafe;color:#1557a6;}
.zone-empty{background:#f8fafc;color:#94a3b8;}
.pitch-frequency{display:flex;flex-wrap:wrap;justify-content:center;gap:7px;margin-top:8px;}
.zone-note{margin-top:10px;color:var(--muted);font-size:12px;line-height:1.45;text-align:center;}
'''
if ".zone-card" not in c:
    css.write_text(c + "\n" + addition, encoding="utf-8")

print("Patched pitch zone UI")
