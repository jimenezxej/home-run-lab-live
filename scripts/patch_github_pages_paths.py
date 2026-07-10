#!/usr/bin/env python3
from pathlib import Path
import re

FILES = [Path("frontend/src/app.js"), Path("app.js")]
MARKER = "HOME_RUN_LAB_GITHUB_PATH_FALLBACK_8_4"

replacement = """// HOME_RUN_LAB_GITHUB_PATH_FALLBACK_8_4
async function loadJSON(path, fallback={}){
  const raw = String(path || "").replace(/^\\/+/, "");
  const filename = raw.split("/").pop();
  const projectBase = window.location.pathname.includes("/home-run-lab-live/")
    ? "/home-run-lab-live/"
    : "./";
  const candidates = [
    path,
    `./${raw}`,
    `./${filename}`,
    `./data/${filename}`,
    `${projectBase}${filename}`,
    `${projectBase}data/${filename}`
  ].filter(Boolean);

  for (const candidate of [...new Set(candidates)]) {
    try {
      const sep = candidate.includes("?") ? "&" : "?";
      const response = await fetch(`${candidate}${sep}v=${Date.now()}`, {cache:"no-store"});
      if (!response.ok) continue;
      return await response.json();
    } catch (error) {}
  }
  console.warn("Unable to load JSON:", path, candidates);
  return fallback;
}"""

patterns = [
    re.compile(r'async\s+function\s+loadJSON\s*\([^)]*\)\s*\{.*?\n\}', re.S),
    re.compile(r'function\s+loadJSON\s*\([^)]*\)\s*\{.*?\n\}', re.S),
]

for file in FILES:
    if not file.exists():
        continue
    text = file.read_text(encoding="utf-8")
    if MARKER in text:
        continue
    changed = False
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            text = text[:match.start()] + replacement + text[match.end():]
            changed = True
            break
    if not changed:
        pos = text.find("function fmt")
        if pos < 0:
            pos = 0
        text = text[:pos] + replacement + "\n\n" + text[pos:]
    file.write_text(text, encoding="utf-8")
    print("Patched", file)
