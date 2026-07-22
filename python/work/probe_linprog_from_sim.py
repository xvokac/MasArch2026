from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from scipy.optimize import linprog


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_detail_txt, read_simplex_dump  # noqa: E402


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
table = read_simplex_dump(root / "zlamal0_1.sim").as_rows_by_header
detail = read_detail_txt(root / "zlamal0_1.txt")

constraint_sets = {
    "rows1_3_rhs_first": (table[1:4, 1:], table[1:4, 0]),
    "rows0_2_rhs_first": (table[0:3, 1:], table[0:3, 0]),
    "rows0_3_rhs_first": (table[0:4, 1:], table[0:4, 0]),
}
objectives = {
    "row0": table[0, 1:],
    "row4": table[4, 1:],
}

print("historical lambda", detail.result.load_factor)
for constraint_name, (A, b) in constraint_sets.items():
    print()
    print(constraint_name, "A", A.shape, "b", b)
    for objective_name, objective in objectives.items():
        for sense, c in [("min", objective), ("max", -objective)]:
            result = linprog(c, A_eq=A, b_eq=b, bounds=[(0, None)] * A.shape[1], method="highs")
            label = f"{sense} {objective_name}"
            print(label, "status", result.status, result.message)
            if not result.success:
                continue
            x = result.x
            print(" fun", result.fun, "row0", table[0, 1:] @ x, "row4", table[4, 1:] @ x)
            print(" nnz", int(np.sum(x > 1e-7)))
            print(" top", [(int(i + 1), float(x[i])) for i in np.argsort(-abs(x))[:8]])

