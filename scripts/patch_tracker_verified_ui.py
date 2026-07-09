#!/usr/bin/env python3
from pathlib import Path
p=Path('frontend/src/app.js'); text=p.read_text(encoding='utf-8')
if 'function last30Dates()' not in text:
    text=text.replace('function hrRows', """function last30Dates(){const out=[];const now=new Date();for(let i=0;i<30;i++){const d=new Date(now);d.setDate(now.getDate()-i);out.push(d.toISOString().slice(0,10));}return out}\nfunction hrRows""",1)
start=text.find('function hrRows(')
if start!=-1:
    ends=[text.find(m,start+1) for m in ['function tracker(','function ai(','function guide(']]; ends=[e for e in ends if e!=-1]
    if ends:
        end=min(ends)
        new="""function hrRows(hrs){
  if(!hrs || !hrs.length){return `<div class=\"card\" style=\"box-shadow:none\"><h3>No verified home runs found for this date yet.</h3><p class=\"sub\">This tracker only shows verified MLB game-feed home runs. If games have not started or feeds have not updated, this date may be empty.</p></div>`;}
  return `<div class=\"table-wrap\"><table><thead><tr><th>Date</th><th>Batter</th><th>Team</th><th>Pitcher</th><th>Inning</th><th>Pitch</th><th>EV</th><th>LA</th><th>Dist</th><th>Source</th><th>Description</th></tr></thead><tbody>${hrs.map(h=>`<tr><td>${fmt(h.date)}</td><td><strong>${fmt(h.batter)}</strong></td><td>${fmt(h.team)}</td><td>${fmt(h.pitcher)}</td><td>${fmt(h.inning)}</td><td>${fmt(h.pitchType)}</td><td>${fmt(h.exitVelocity)}</td><td>${fmt(h.launchAngle)}</td><td>${fmt(h.distance)}</td><td><span class=\"status-tag verified\">MLB Feed</span></td><td class=\"wrap\">${fmt(h.description)}</td></tr>`).join(\"\")}</tbody></table></div>`;
}
"""
        text=text[:start]+new+'\n'+text[end:]
start=text.find('function tracker(){')
if start!=-1:
    ends=[text.find(m,start+1) for m in ['function ai(','function guide(','function glossary(']]; ends=[e for e in ends if e!=-1]
    if ends:
        end=min(ends)
        new="""function tracker(){
  const hist=state.history||{}; const byDate=hist.byDate||{}; const hrs=hist.home_runs||[]; const dates=(hist.dates&&hist.dates.length)?hist.dates:last30Dates();
  return `${hero(\"HR Tracker\",\"Verified MLB home run history by date. Choose any of the last 30 days to review actual home run hitters, pitcher allowed, pitch info, EV, LA, and distance where available.\")}
  <section class=\"card\"><div class=\"lab-note\">Source: ${fmt(hist.source,\"MLB Stats API game feed\")}. Rule: ${fmt(hist.verifiedRule,\"Only verified home-run plays are included.\")}</div><br><div class=\"searchbar\"><select id=\"dateFilter\"><option value=\"\">All dates</option>${dates.map(d=>`<option>${d}</option>`).join(\"\")}</select><input id=\"playerFilter\" placeholder=\"Filter player...\" /></div><div id=\"trackerCount\" class=\"sub\" style=\"text-align:center;margin-bottom:12px\">${hrs.length} verified HRs loaded.</div><div id=\"trackerTable\">${hrRows(hrs)}</div></section>`;
}
"""
        text=text[:start]+new+'\n'+text[end:]
old='''if(state.tab==="tracker"){const dateFilter=$("#dateFilter"),playerFilter=$("#playerFilter");const apply=()=>{const d=dateFilter.value,q=playerFilter.value.toLowerCase();const rows=(state.history?.home_runs||[]).filter(h=>(!d||h.date===d)&&(!q||String(h.batter||"").toLowerCase().includes(q)));$("#trackerTable").innerHTML=hrRows(rows)};dateFilter.addEventListener("change",apply);playerFilter.addEventListener("input",apply)}'''
new='''if(state.tab==="tracker"){const dateFilter=$("#dateFilter"),playerFilter=$("#playerFilter");const apply=()=>{const d=dateFilter.value,q=playerFilter.value.toLowerCase();const byDate=state.history?.byDate||{};const base=d?(byDate[d]||[]):(state.history?.home_runs||[]);const rows=base.filter(h=>(!q||String(h.batter||"").toLowerCase().includes(q)));$("#trackerCount").textContent=`${rows.length} verified HRs ${d?`on ${d}`:"loaded"}.`;$("#trackerTable").innerHTML=hrRows(rows)};dateFilter.addEventListener("change",apply);playerFilter.addEventListener("input",apply)}'''
if old in text: text=text.replace(old,new)
else: print('Warning: tracker binding pattern not found; UI view patched, test dropdown manually.')
p.write_text(text,encoding='utf-8')
print('Patched verified HR tracker UI')
