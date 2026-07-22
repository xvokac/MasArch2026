from __future__ import annotations

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
G = ab.transform_joint_loads(detail.transformed_masonry + detail.transformed_fill)
Q = ab.transform_joint_loads(detail.transformed_external)
C = np.zeros((3, n))
C[0] = table[2, :n]
C[1] = table[3, 1 : n + 1]
C[2, : n - 1] = table[4, 2 : n + 1]
A = np.column_stack([Q, C.T])

for sign_a in [1, -1]:
    for sign_b in [1, -1]:
        for objective in ([1, 0, 0, 0], [-1, 0, 0, 0]):
            result = linprog(
                objective,
                A_ub=sign_a * A,
                b_ub=sign_b * G,
                bounds=[(None, None)] * 4,
                method="highs",
            )
            print()
            print("sign_a", sign_a, "sign_b", sign_b, "objective", objective)
            print(result.status, result.message)
            if result.success:
                slack = sign_a * A @ result.x - sign_b * G
                print("x", result.x, "fun", result.fun)
                print("load candidates", result.x[0], -result.x[0])
                print("tight", [(int(i + 1), float(slack[i])) for i in np.argsort(abs(slack))[:8]])

