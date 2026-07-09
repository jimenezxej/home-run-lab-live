#!/usr/bin/env python3
from pathlib import Path

p = Path("frontend/src/app.js")
text = p.read_text(encoding="utf-8")

text = text.replace("pitchZones:null, updateStatus:null, glossary:null", "pitchZones:null, updateStatus:null, intelligence:null, glossary:null")
if 'intelligence.json' not in text:
    text = text.replace(
        'state.updateStatus=await loadJSON("update-status.json",{});',
        'state.updateStatus=await loadJSON("update-status.json",{});\n  state.intelligence=await loadJSON("intelligence.json",{paperBoard:[],longshotBoard:[]});'
    )

helper = """
function paperPlayers(){
  const rows = [...players()];
  return rows.sort((a,b)=>(b.intelligence?.paperScore||0)-(a.intelligence?.paperScore||0));
}
function longshotPlayers(){
  const rows = [...players()].filter(p=>{
    const pa = Number(p.profile?.sampleSize||0);
    const paperRank = Number(p.intelligence?.paperRank||999);
    return pa >= 35 && paperRank > 8;
  });
  return rows.sort((a,b)=>(b.intelligence?.longshotScore||0)-(a.intelligence?.longshotScore||0));
}
"""
if "function paperPlayers()" not in text:
    idx = text.find("function playerTable")
    if idx != -1:
        text = text[:idx] + helper + "\n" + text[idx:]
    else:
        text += "\n" + helper

start = text.find("function hrlab(){")
if start != -1:
    end = text.find("function longshotRows", start)
    if end == -1:
        end = text.find("function longshots", start)
    if end != -1:
        new_hrlab = """
function hrlab(){
  const rows = paperPlayers();
  return `${hero("Home Run Lab","Best home run spots on paper. This board prioritizes proven sample, season HR power, matchup, weather, confidence, and overall HR profile.")}
  <section class="card"><div class="lab-note">This is the clean main board, not the sleeper board. Look for strong PA sample, real season HR production, pitcher vulnerability, and weather support.</div><br>${playerTable(rows.slice(0,80))}</section>`;
}
"""
        text = text[:start] + new_hrlab + "\n" + text[end:]

start = text.find("function longshotRows(){")
if start != -1:
    end = text.find("function longshots(){", start)
    if end != -1:
        text = text[:start] + text[end:]

start = text.find("function longshots(){")
if start != -1:
    end_candidates = [text.find(marker, start+1) for marker in ["function qClass", "function pitchers", "function weather"]]
    end_candidates = [x for x in end_candidates if x != -1]
    if end_candidates:
        end = min(end_candidates)
        new_longshots = """
function longshots(){
  const rows = longshotPlayers();
  return `${hero("Longshot Lab","Under-the-radar HR threats. This board intentionally avoids simply copying the top Home Run Lab plays.")}
  <section class="card">
    <div class="lab-note">Longshots are not the safest plays. They are overlooked profiles with enough sample, real pop, a targetable pitcher, weather/park help, or lower-lineup leverage. Obvious top paper plays are penalized here.</div>
    <br>${playerTable(rows.slice(0,80))}
  </section>`;
}
"""
        text = text[:start] + new_longshots + "\n" + text[end:]

if "<th>Paper</th><th>Longshot</th>" not in text:
    text = text.replace("<th>HR Edge</th><th>Prob</th>", "<th>Paper</th><th>Longshot</th><th>HR Edge</th><th>Prob</th>")
    text = text.replace(
        '<td>${badgeMetric("hr_edge",p.scores?.hr_edge)}</td><td>${badgeMetric("prob",p.scores?.model_probability,"%")}</td>',
        '<td>${badgeMetric("hr_edge",p.intelligence?.paperScore)}</td><td>${badgeMetric("hr_edge",p.intelligence?.longshotScore)}</td><td>${badgeMetric("hr_edge",p.scores?.hr_edge)}</td><td>${badgeMetric("prob",p.scores?.model_probability,"%")}</td>'
    )

p.write_text(text, encoding="utf-8")
print("Patched 7.0 UI: separate Home Run Lab and Longshot Lab boards")
