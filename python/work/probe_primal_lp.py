from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from scipy.optimize import linprog


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_detail_txt, read_simplex_dump  # noqa: E402


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
dump = read_simplex_dump(root / "zlamal0_1.sim")
detail = read_detail_txt(root / "zlamal0_1.txt")
matrix = dump.values[:825].reshape((165, 5))
active = [item.variable_index - 1 for item in detail.result.local_deformations]

print("row0", matrix[0])
print("active rows")
print(matrix[active])

for rhs_col in range(5):
    A = np.delete(matrix[active], rhs_col, axis=1)
    b = matrix[active, rhs_col]
    try:
        solution = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        continue
    print("rhs_col", rhs_col, "solution", solution)

print()
print("linprog variants")
for skip_objective in [False, True]:
    rows = matrix[1:] if skip_objective else matrix[:164]
    objective_row = matrix[0] if skip_objective else matrix[164]
    for rhs_col in range(5):
        Araw = np.delete(rows, rhs_col, axis=1)
        braw = rows[:, rhs_col]
        craw = np.delete(objective_row, rhs_col)
        for sense, A_ub, b_ub in [
            ("le", Araw, braw),
            ("ge", -Araw, -braw),
        ]:
            for obj_sense, c in [("min", craw), ("max", -craw)]:
                result = linprog(
                    c,
                    A_ub=A_ub,
                    b_ub=b_ub,
                    bounds=[(None, None)] * 4,
                    method="highs",
                )
                if not result.success:
                    continue
                active_slack = Araw @ result.x - braw
                tight = np.argsort(abs(active_slack))[:4].tolist()
                tight_1based = [item + (2 if skip_objective else 1) for item in tight]
                value = craw @ result.x
                print(
                    "skip_obj",
                    skip_objective,
                    "rhs",
                    rhs_col,
                    sense,
                    obj_sense,
                    "fun",
                    result.fun,
                    "value",
                    value,
                    "x",
                    result.x,
                    "tight",
                    tight_1based,
                )

