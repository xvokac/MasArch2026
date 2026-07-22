from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_ab_dump, read_detail_txt  # noqa: E402


def state_vector(*columns: np.ndarray) -> np.ndarray:
    return np.column_stack(columns).ravel()


root = Path(r"D:\Documents\2026\MASARCH2026\masarch\zlamal0")
ab = read_ab_dump(root / "zlamal0_1.AB", block_count=40)
detail = read_detail_txt(root / "zlamal0_1.txt")

normal = detail.result.normal_forces
shear = detail.result.shear_forces
distance_from_top = detail.result.normal_distances
thickness = 0.145
moment_top = normal * distance_from_top
moment_bottom = normal * (thickness - distance_from_top)
moment_mid = normal * (distance_from_top - thickness / 2.0)

print("AB", ab.matrix.shape)
print("detail vectors", normal.shape, shear.shape, distance_from_top.shape)
print("active local deformations")
for item in detail.result.local_deformations:
    print(item)

variants = {
    "N,T,e": state_vector(normal, shear, distance_from_top),
    "N,T,N*e_top": state_vector(normal, shear, moment_top),
    "N,T,N*(h-e)": state_vector(normal, shear, moment_bottom),
    "N,T,N*(e-h/2)": state_vector(normal, shear, moment_mid),
    "T,N,N*e_top": state_vector(shear, normal, moment_top),
    "N,M_top,T": state_vector(normal, moment_top, shear),
}

for name, vector in variants.items():
    product = ab.matrix @ vector
    print()
    print(name)
    print("range", float(product.min()), float(product.max()))
    print("active rows")
    for item in detail.result.local_deformations:
        row = item.variable_index - 1
        print(row + 1, item.value, product[row])
    print("first phi rows", product[:12])
    print("first sliding rows", product[2 * ab.joint_count : 2 * ab.joint_count + 12])

print()
print("load-vector hypotheses from transformed loads")
permanent = detail.transformed_masonry + detail.transformed_fill
variable = detail.transformed_external
for name, vector in {
    "g": permanent.ravel(),
    "q": variable.ravel(),
    "g+lambda*q": (permanent + detail.result.load_factor * variable).ravel(),
    "-(g+lambda*q)": -(permanent + detail.result.load_factor * variable).ravel(),
}.items():
    product = ab.matrix @ vector
    print()
    print(name)
    print("range", float(product.min()), float(product.max()))
    for item in detail.result.local_deformations:
        row = item.variable_index - 1
        print(row + 1, item.value, product[row])
    print("first phi rows", product[:12])
    print("phi active-ish sorted", [(int(i + 1), float(product[i])) for i in np.argsort(abs(product[: 2 * ab.joint_count]))[:8]])

print()
print("global force hypotheses from N/T/d")
xy = detail.intrados_extrados
intr = xy[:, :2]
extr = xy[:, 2:]
radial_out = extr - intr
radial_out = radial_out / np.linalg.norm(radial_out, axis=1)[:, None]
radial_in = -radial_out
rot_left = np.column_stack([-radial_out[:, 1], radial_out[:, 0]])
rot_right = np.column_stack([radial_out[:, 1], -radial_out[:, 0]])
point = extr + (distance_from_top / thickness)[:, None] * (intr - extr)
directions = {
    "N=left,T=out": (rot_left, radial_out),
    "N=left,T=in": (rot_left, radial_in),
    "N=right,T=out": (rot_right, radial_out),
    "N=right,T=in": (rot_right, radial_in),
}
for name, (n_dir, t_dir) in directions.items():
    force = normal[:, None] * n_dir + shear[:, None] * t_dir
    moment = point[:, 0] * force[:, 1] - point[:, 1] * force[:, 0]
    for colname, vec in {
        "Fx,Fy,M": state_vector(force[:, 0], force[:, 1], moment),
        "Fx,Fy,-M": state_vector(force[:, 0], force[:, 1], -moment),
        "Fy,Fx,M": state_vector(force[:, 1], force[:, 0], moment),
    }.items():
        product = ab.matrix @ vec
        active = [abs(product[item.variable_index - 1]) for item in detail.result.local_deformations]
        print(name, colname, "active_abs", active, "range", float(product.min()), float(product.max()))
