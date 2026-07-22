from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from scipy.optimize import linprog


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_simplex_dump  # noqa: E402


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
blocks = read_simplex_dump(root / "zlamal0_1.sim").streamed_blocks
A = np.column_stack([blocks[1], blocks[2], blocks[3], blocks[4]])
for sign_a in [1, -1]:
    for sign_b in [1, -1]:
        result = linprog(
            [-1, 0, 0, 0],
            A_ub=sign_a * A,
            b_ub=sign_b * blocks[0],
            bounds=[(None, None)] * 4,
            method="highs",
        )
        print(sign_a, sign_b, result.status, result.x[0] if result.success else result.message)
