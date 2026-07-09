#!/usr/bin/env python3
from pathlib import Path
p = Path("backend/model/scoring.py")
text = p.read_text(encoding="utf-8")
# lightweight patch: add identity warning to reasons if scoring.py has reasons list pattern
needle = 'if not h.get("seasonStatsVerified"): reasons.append("Season PA/H/HR are not verified for this hitter yet; sample confidence reduced.")'
if needle in text and 'identityTrusted' not in text[text.find(needle):text.find(needle)+500]:
    repl = needle + '\n    if not h.get("identityTrusted", True): reasons.append("Player identity is unresolved or suspicious; confidence reduced until MLBAM ID is verified.")'
    text = text.replace(needle, repl)
p.write_text(text, encoding="utf-8")
print("Patched scoring identity guard")
