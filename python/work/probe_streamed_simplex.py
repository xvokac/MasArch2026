from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from scipy.optimize import linprog


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_ab_dump, read_detail_txt, read_simplex_dump  # noqa: E402


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
dump = read_simplex_dump(root / "zlamal0_1.sim")
detail = read_detail_txt(root / "zlamal0_1.txt")
ab = read_ab_dump(root / "zlamal0_1.AB", detail.block_count)
n = dump.nr_variable_count
values = dump.values

xh = np.zeros(n)
for item in detail.result.local_deformations:
    xh[item.variable_index - 1] = item.value

blocks = [values[i * n : (i + 1) * n] for i in range(5)]
print("value count", len(values))
for i, block in enumerate(blocks):
    print(i, "dot", float(block @ xh), "first12", block[:12], "last3", block[-3:])
print("tail", values[5 * n :])

G = ab.transform_joint_loads(detail.transformed_masonry + detail.transformed_fill)
Q = ab.transform_joint_loads(detail.transformed_external)
print("max block0+G", float(np.max(np.abs(blocks[0] + G))))
print("max block1-Q", float(np.max(np.abs(blocks[1] - Q))))

Aeq = np.vstack([blocks[1], blocks[2], blocks[3], blocks[4]])
beq = np.array([1.0, 0.0, 0.0, 0.0])
result = linprog(G, A_eq=Aeq, b_eq=beq, bounds=[(0, None)] * n, method="highs")
print("linprog", result.status, result.message)
if result.success:
    print("lambda", -result.fun, "historic", detail.result.load_factor)
    print("nnz", int(np.sum(result.x > 1e-7)))
    print("top", [(int(i + 1), float(result.x[i])) for i in np.argsort(-abs(result.x))[:8]])
    print("residual", Aeq @ result.x - beq)

