#!/usr/bin/env python3
from pathlib import Path
p=Path("frontend/src/app.js")
text=p.read_text(encoding="utf-8")
text=text.replace("pitchZones:null, glossary:null", "pitchZones:null, updateStatus:null, glossary:null")
if 'update-status.json' not in text:
    text=text.replace('state.pitchZones=await loadJSON("pitch-zone-profiles.json",{profiles:{}});',
                      'state.pitchZones=await loadJSON("pitch-zone-profiles.json",{profiles:{}});\n  state.updateStatus=await loadJSON("update-status.json",{});')
# Lightly enhance dashboard text if possible
old='A control room for today\'s slate.'
if old in text:
    text=text.replace(old, 'A control room for today\'s slate. Auto-updates lineups and probable pitchers during the day.')
p.write_text(text,encoding="utf-8")
print("Patched update status UI loader")
