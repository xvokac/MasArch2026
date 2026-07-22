from __future__ import annotations

from pathlib import Path
import re
import struct

import numpy as np


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
ab_path = root / "zlamal0_1.AB"
txt_path = root / "zlamal0_1.txt"
data = ab_path.read_bytes()
values = np.array(struct.unpack("<" + "f" * (len(data) // 4), data), dtype=float)

n_blocks = 40
n_joints = n_blocks + 1
row_major = values.reshape((4 * n_joints, 3 * n_joints))
col_major = values.reshape((3 * n_joints, 4 * n_joints))

print("float_count", values.size)
print("row_major", row_major.shape, "col_major", col_major.shape)
print("row-major nonzeros first 12 rows")
for row in range(12):
    nz = np.flatnonzero(abs(row_major[row]) > 1e-12)
    print(row, len(nz), nz[:12].tolist(), row_major[row, nz[:12]])
print()
print("row-major nonzeros selected rows")
for row in [0, 1, 2, 3, 4, 40, 41, 81, 82, 123, 124, 163]:
    nz = np.flatnonzero(abs(row_major[row]) > 1e-12)
    print(row, len(nz), nz[:8].tolist(), row_major[row, nz[:8]])

print()
print("first row as triples")
print(row_major[0].reshape((n_joints, 3))[:10])

text = txt_path.read_text(encoding="cp1250", errors="ignore")
result = re.search(
    r"Vektor normalovych sil.*?\n([+\-0-9\.\t ]+)\s*\n Vektor vzdalenosti",
    text,
    re.S,
)
if result:
    normals = np.array([float(item) for item in result.group(1).split()])
    print()
    print("normals", normals.shape, normals[:10])
    products = row_major @ np.repeat(normals, 3)[: row_major.shape[1]]
    print("dummy product range", products.min(), products.max(), products[:10])
