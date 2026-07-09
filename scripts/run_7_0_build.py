#!/usr/bin/env python3
import subprocess
cmds = [
    ["python3", "backend/model/intelligence_engine.py"],
    ["python3", "scripts/patch_7_0_ui.py"],
    ["python3", "scripts/build_github_pages.py"],
    ["python3", "scripts/check_7_0_boards.py"],
]
for cmd in cmds:
    print("RUN:", " ".join(cmd))
    subprocess.run(cmd, check=True)
