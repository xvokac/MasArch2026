from __future__ import annotations

import subprocess
import sys


CODE = r"""
from pathlib import Path
from march import analyze, parse_input, render_output
from tests.test_march_examples import _primary_result

stem = __import__("sys").argv[1]
base = Path(r"D:\Documents\2026\MASARCH2026\MArch")
data = parse_input(base / f"{stem}.txt")
result = analyze(data, list_generated=False)
print(_primary_result(render_output(result, f"{stem}.txt")))
"""


for stem in ["in1", "in2", "in3", "input", "dukovany_in", "klenba"]:
    try:
        result = subprocess.run(
            [sys.executable, "-c", CODE, stem],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        print(stem, "TIMEOUT")
        continue
    print(stem, "RC", result.returncode, (result.stdout or result.stderr).strip())
