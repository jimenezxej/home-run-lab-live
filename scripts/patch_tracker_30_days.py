#!/usr/bin/env python3
from pathlib import Path
p = Path("frontend/src/app.js")
text = p.read_text(encoding="utf-8")
inject = '''
function last30Dates(){
  const out=[];
  const now=new Date();
  for(let i=0;i<30;i++){
    const d=new Date(now);
    d.setDate(now.getDate()-i);
    out.push(d.toISOString().slice(0,10));
  }
  return out;
}
'''
if "function last30Dates()" not in text:
    text = text.replace("const state = ", inject + "\nconst state = ", 1)
text = text.replace("const hrs=state.history?.home_runs||[],dates=[...new Set(hrs.map(h=>h.date).filter(Boolean))].sort().reverse();", "const hrs=state.history?.home_runs||[],dates=last30Dates();")
p.write_text(text, encoding="utf-8")
print("Patched tracker date dropdown to last 30 days")
