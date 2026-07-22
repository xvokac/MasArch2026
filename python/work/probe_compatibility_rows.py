from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_detail_txt, read_simplex_dump  # noqa: E402


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
table = read_simplex_dump(root / "zlamal0_1.sim").as_rows_by_header
detail = read_detail_txt(root / "zlamal0_1.txt")
x = np.zeros(164)
for item in detail.result.local_deformations:
    x[item.variable_index - 1] = item.value


def shifted(row: np.ndarray, offset: int) -> np.ndarray:
    coeff = np.zeros(164)
    source = row
    for j in range(164):
        k = j + offset
        if 0 <= k < len(source):
            coeff[j] = source[k]
    return coeff


for row_index in range(5):
    print()
    print("row", row_index)
    candidates = []
    for offset in range(-5, 8):
        coeff = shifted(table[row_index], offset)
        value = float(coeff @ x)
        norm = float(np.linalg.norm(coeff))
        candidates.append((abs(value), offset, value, norm, coeff[:12].tolist()))
    for _, offset, value, norm, head in sorted(candidates)[:6]:
        print(" offset", offset, "dot", value, "norm", norm, "head", head)

rot = np.ravel(np.column_stack([np.ones(41), -np.ones(41)]))
rot = np.concatenate([rot, np.zeros(82)])
print()
print("manual rotation dot", float(rot @ x), "head", rot[:12].tolist())

