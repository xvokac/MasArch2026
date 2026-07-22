from __future__ import annotations

from pathlib import Path
import struct

import numpy as np
from scipy.optimize import linprog


path = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0\zlamal0_1.sim")
data = path.read_bytes()
nvar, nrow, sense = struct.unpack("<3i", data[:12])
values = np.array(struct.unpack("<" + "f" * ((len(data) - 12) // 4), data[12:]), float)
tableau = values[: (nrow + 1) * (nvar + 1)].reshape((nrow + 1, nvar + 1))
A = tableau[:nrow, :nvar].copy()
b = tableau[:nrow, -1].copy()
c = tableau[nrow, :nvar].copy()
A[abs(A) < 1e-38] = 0.0
b[abs(b) < 1e-38] = 0.0
c[abs(c) < 1e-38] = 0.0

print("header", nvar, nrow, sense)
print("first raw float/int cells")
for index in range(20):
    chunk = data[12 + 4 * index : 12 + 4 * index + 4]
    print(index, struct.unpack("<f", chunk)[0], struct.unpack("<i", chunk)[0])
print("last raw float/int cells")
total_cells = (len(data) - 12) // 4
for index in range(total_cells - 10, total_cells):
    chunk = data[12 + 4 * index : 12 + 4 * index + 4]
    print(index, struct.unpack("<f", chunk)[0], struct.unpack("<i", chunk)[0])
print("rhs", b)
print("nonzero c", np.count_nonzero(c), "c min/max", c.min(), c.max())

variants = [
    ("eq_min_c", A, b, None, None, c),
    ("eq_max_c", A, b, None, None, -c),
    ("le_min_c", None, None, A, b, c),
    ("le_max_c", None, None, A, b, -c),
    ("ge_min_c", None, None, -A, -b, c),
    ("ge_max_c", None, None, -A, -b, -c),
]

for name, Aeq, beq, Aub, bub, objective in variants:
    result = linprog(
        objective,
        A_ub=Aub,
        b_ub=bub,
        A_eq=Aeq,
        b_eq=beq,
        bounds=[(0, None)] * nvar,
        method="highs",
    )
    print()
    print(name, "status", result.status, result.message)
    if not result.success:
        continue
    x = result.x
    print("fun", result.fun, "c@x", c @ x, "nnz", int(np.sum(x > 1e-7)))
    print("top", [(int(i + 1), float(x[i])) for i in np.argsort(-abs(x))[:10]])
    print("active rows", A @ x - b)

print()
print("alternate 164 inequalities x 4 variables")
alt = values[:165 * 5].reshape((165, 5))
alt_A = alt[:164, :4].copy()
alt_b = alt[:164, 4].copy()
alt_c = alt[164, :4].copy()
alt_A[abs(alt_A) < 1e-38] = 0.0
alt_b[abs(alt_b) < 1e-38] = 0.0
alt_c[abs(alt_c) < 1e-38] = 0.0
print("c", alt_c, "rhs range", alt_b.min(), alt_b.max(), "nonzero rhs", np.count_nonzero(alt_b))
for name, Aub, bub, objective in [
    ("le_min", alt_A, alt_b, alt_c),
    ("le_max", alt_A, alt_b, -alt_c),
    ("ge_min", -alt_A, -alt_b, alt_c),
    ("ge_max", -alt_A, -alt_b, -alt_c),
]:
    result = linprog(
        objective,
        A_ub=Aub,
        b_ub=bub,
        bounds=[(None, None)] * 4,
        method="highs",
    )
    print()
    print(name, "status", result.status, result.message)
    if not result.success:
        continue
    x = result.x
    slack = alt_A @ x - alt_b
    print("fun", result.fun, "c@x", alt_c @ x, "x", x)
    print("tight", [(int(i + 1), float(slack[i])) for i in np.argsort(abs(slack))[:10]])
