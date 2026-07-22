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

print("x nnz", [(int(i + 1), float(x[i])) for i in np.flatnonzero(x)])

for layout, A, b in [
    ("rhs_first_all", table[:, 1:], table[:, 0]),
    ("rhs_last_all", table[:, :-1], table[:, -1]),
]:
    y = A @ x
    print()
    print(layout)
    print("Ax", y)
    print("b", b)
    print("Ax-b", y - b)
    print("ratios", [float(y[i] / b[i]) if abs(b[i]) > 1e-12 else None for i in range(len(b))])

print()
print("single row dot products using active variables")
for row in range(table.shape[0]):
    print(row, "first_rhs", float(table[row, 1:] @ x), "rhs", float(table[row, 0]))
    print(row, "last_rhs", float(table[row, :-1] @ x), "rhs", float(table[row, -1]))

