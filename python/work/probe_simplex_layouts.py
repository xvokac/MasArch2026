from __future__ import annotations

from itertools import combinations
from pathlib import Path
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_detail_txt, read_simplex_dump  # noqa: E402


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
table = read_simplex_dump(root / "zlamal0_1.sim").as_rows_by_header
detail = read_detail_txt(root / "zlamal0_1.txt")
basis = [item.variable_index - 1 for item in detail.result.local_deformations]
historic = np.array([item.value for item in detail.result.local_deformations], dtype=float)

print("basis", basis, "historic", historic)

tests: list[tuple[str, np.ndarray, np.ndarray]] = []
for rows in combinations(range(table.shape[0]), 4):
    rows = list(rows)
    tests.append((f"rows{rows}_rhs_first", table[rows, 1:], table[rows, 0]))
    tests.append((f"rows{rows}_rhs_last", table[rows, :-1], table[rows, -1]))

for name, A, b in tests:
    try:
        x = np.linalg.solve(A[:, basis], b)
    except np.linalg.LinAlgError:
        continue
    if not np.all(np.isfinite(x)):
        continue
    scale = float(np.dot(x, historic) / np.dot(historic, historic))
    residual = np.linalg.norm(x - scale * historic)
    direct = np.linalg.norm(x - historic)
    if residual < 1.0 or direct < 1.0:
        print(name, "x", x, "scale", scale, "residual", residual, "direct", direct)

