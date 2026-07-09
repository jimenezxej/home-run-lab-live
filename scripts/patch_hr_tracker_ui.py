#!/usr/bin/env python3
from pathlib import Path

p = Path("frontend/src/app.js")
text = p.read_text(encoding="utf-8")

if "function trackerDates()" not in text:
    helper = """
function trackerDates(){
  const hist = state.history || {};
  if(hist.dates && hist.dates.length) return hist.dates;
  const out=[];
  const now=new Date();
  for(let i=0;i<30;i++){
    const d=new Date(now);
    d.setDate(now.getDate()-i);
    out.push(d.toISOString().slice(0,10));
  }
  return out;
}
function trackerRowsForDate(dateValue){
  const hist = state.history || {};
  const byDate = hist.byDate || {};
  if(dateValue) return byDate[dateValue] || [];
  return hist.home_runs || [];
}
"""
    idx = text.find("function hrRows")
    if idx != -1:
        text = text[:idx] + helper + "\n" + text[idx:]
    else:
        text += "\n" + helper

start = text.find("function hrRows(")
if start != -1:
    ends = [text.find(marker, start+1) for marker in ["function tracker(", "function ai(", "function guide(", "function glossary("]]
    ends = [x for x in ends if x != -1]
    if ends:
        end = min(ends)
        new_func = """
function hrRows(hrs){
  if(!hrs || !hrs.length){
    return `<div class="card" style="box-shadow:none"><h3>No verified home runs found for this date.</h3><p class="sub">This means either there were no MLB home runs on that date, games have not started, or the MLB feed did not return HR plays yet.</p></div>`;
  }
  return `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Batter</th><th>Team</th><th>Pitcher</th><th>Inning</th><th>Pitch</th><th>EV</th><th>LA</th><th>Dist</th><th>Verified</th><th>Description</th></tr></thead><tbody>${hrs.map(h=>`<tr><td>${fmt(h.date)}</td><td><strong>${fmt(h.batter)}</strong></td><td>${fmt(h.team)}</td><td>${fmt(h.pitcher)}</td><td>${fmt(h.inning)}</td><td>${fmt(h.pitchType)}</td><td>${fmt(h.exitVelocity)}</td><td>${fmt(h.launchAngle)}</td><td>${fmt(h.distance)}</td><td><span class="status-tag verified">MLB</span></td><td class="wrap">${fmt(h.description)}</td></tr>`).join("")}</tbody></table></div>`;
}
"""
        text = text[:start] + new_func + "\n" + text[end:]

start = text.find("function tracker(){")
if start != -1:
    ends = [text.find(marker, start+1) for marker in ["function ai(", "function guide(", "function glossary(", "function render("]]
    ends = [x for x in ends if x != -1]
    if ends:
        end = min(ends)
        new_tracker = """
function tracker(){
  const hist = state.history || {};
  const dates = trackerDates();
  const hrs = hist.home_runs || [];
  return `${hero("HR Tracker","Verified MLB home run history. Select any of the last 30 dates to see actual home runs from the MLB game feed.")}
  <section class="card">
    <div class="lab-note">Source: ${fmt(hist.source,"MLB Stats API game feed")} | Updated: ${fmt(hist.updatedAt,"N/A")} | Loaded HRs: ${hrs.length}</div>
    <br>
    <div class="searchbar">
      <select id="dateFilter"><option value="">All dates</option>${dates.map(d=>`<option value="${d}">${d}</option>`).join("")}</select>
      <input id="playerFilter" placeholder="Filter player..." />
    </div>
    <div id="trackerCount" class="sub" style="text-align:center;margin-bottom:12px">${hrs.length} verified HRs loaded.</div>
    <div id="trackerTable">${hrRows(hrs)}</div>
  </section>`;
}
"""
        text = text[:start] + new_tracker + "\n" + text[end:]

# Replace render tracker event block conservatively
idx = text.find('if(state.tab==="tracker"){')
if idx != -1:
    end = text.find('if(state.tab===', idx + 1)
    if end == -1:
        end = text.find('}', idx) + 1
    block = text[idx:end]
    if "dateFilter" in block and "trackerTable" in block:
        new_block = """if(state.tab==="tracker"){
  const dateFilter=$("#dateFilter"), playerFilter=$("#playerFilter");
  const apply=()=>{
    const d=dateFilter.value;
    const q=(playerFilter.value||"").toLowerCase();
    const base=trackerRowsForDate(d);
    const rows=base.filter(h=>!q||String(h.batter||"").toLowerCase().includes(q));
    $("#trackerCount").textContent=`${rows.length} verified HRs ${d?`on ${d}`:"loaded"}.`;
    $("#trackerTable").innerHTML=hrRows(rows);
  };
  dateFilter.addEventListener("change",apply);
  playerFilter.addEventListener("input",apply);
}
"""
        text = text[:idx] + new_block + text[end:]

p.write_text(text, encoding="utf-8")
print("Patched HR Tracker UI")
