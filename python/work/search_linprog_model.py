from __future__ import annotations

from itertools import combinations
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import linprog


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_ab_dump, read_detail_txt, read_simplex_dump  # noqa: E402


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
detail = read_detail_txt(root / "zlamal0_1.txt")
ab = read_ab_dump(root / "zlamal0_1.AB", detail.block_count)
table = read_simplex_dump(root / "zlamal0_1.sim").as_rows_by_header
n = 4 * detail.joint_count

xh = np.zeros(n)
for item in detail.result.local_deformations:
    xh[item.variable_index - 1] = item.value


def shift(row: np.ndarray, offset: int) -> np.ndarray:
    out = np.zeros(n)
    for j in range(n):
        k = j + offset
        if 0 <= k < len(row):
            out[j] = row[k]
    return out


rows: list[tuple[str, np.ndarray, float]] = []
for row_index in range(table.shape[0]):
    for offset in range(-5, 8):
        coeff = shift(table[row_index], offset)
        rows.append((f"r{row_index}_o{offset}", coeff, float(coeff @ xh)))

print("rows close to 0")
for name, _, value in sorted(rows, key=lambda item: abs(item[2]))[:12]:
    print(name, value)
print()
print("rows close to 1")
for name, _, value in sorted(rows, key=lambda item: abs(item[2] - 1.0))[:12]:
    print(name, value)

G = ab.transform_joint_loads(detail.transformed_masonry + detail.transformed_fill)
Q = ab.transform_joint_loads(detail.transformed_external)
zero_candidates = [(name, coeff) for name, coeff, value in rows if abs(value) < 1e-4]
one_candidates = [("ABQ", Q)] + [(name, coeff) for name, coeff, value in rows if abs(value - 1.0) < 1e-4]

print()
print("LP candidates")
for one_name, one_row in one_candidates[:8]:
    for zero_count in [3, 4, 5]:
      for zeros in combinations(zero_candidates[:12], zero_count):
        Aeq = np.vstack([one_row, *[item[1] for item in zeros]])
        beq = np.array([1.0] + [0.0] * zero_count)
        result = linprog(G, A_eq=Aeq, b_eq=beq, bounds=[(0, None)] * n, method="highs")
        if not result.success:
            continue
        top = [(int(i + 1), float(result.x[i])) for i in np.argsort(-abs(result.x))[:4]]
        if abs(-result.fun - detail.result.load_factor) < 1e-4:
            print("MATCH", one_name, [item[0] for item in zeros], -result.fun, top)
        elif -result.fun < detail.result.load_factor + 1.0:
            print("near", one_name, [item[0] for item in zeros], -result.fun, top)
