#!/usr/bin/env python3
from pathlib import Path
p=Path("frontend/src/app.js")
text=p.read_text(encoding="utf-8")
helper = """
function statusTag(status){
  if(!status) return "";
  const s=String(status).toLowerCase();
  return `<span class="status-tag ${s}">${s}</span>`;
}
"""
if "function statusTag(" not in text:
    text=text.replace("const state = ", helper+"\nconst state = ",1)
text=text.replace("<li>Stack score: ${fmt(p.scores?.stack_score)}</li>", "<li>Stack score: ${fmt(p.scores?.stack_score)}</li><li>Pitcher fields used: ${fmt((p.provenance?.pitcherFieldsUsed||[]).join(', '),'N/A')}</li><li>ISO status: ${fmt(p.provenance?.isoStatus)}</li><li>xwOBAcon status: ${fmt(p.provenance?.xwobaconStatus)}</li>")
p.write_text(text,encoding="utf-8")

css=Path("frontend/src/styles.css")
c=css.read_text(encoding="utf-8")
add = """
.status-tag{display:inline-flex;border-radius:999px;padding:3px 7px;font-size:10px;font-weight:950;text-transform:uppercase;border:1px solid currentColor;margin-left:4px;}
.status-tag.verified{color:#047857;background:#d1fae5;}
.status-tag.calculated{color:#1557a6;background:#dbeafe;}
.status-tag.estimated{color:#9a3412;background:#ffedd5;}
.status-tag.missing{color:#475569;background:#f1f5f9;}
"""
if ".status-tag" not in c:
    css.write_text(c+"\n"+add,encoding="utf-8")
print("Patched verified UI helpers")
