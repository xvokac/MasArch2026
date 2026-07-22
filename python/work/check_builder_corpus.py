from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import (  # noqa: E402
    load_zlamal_cases,
    prepare_melb_input,
    read_ab_dump,
    read_melb_input,
    read_simplex_bytes,
    read_simplex_dump,
)


ROOT = Path(r"D:\Documents\2026\MASARCH2026\masarch")


def main() -> None:
    rows = []
    for case in load_zlamal_cases(ROOT):
        base = case.input_path.with_suffix("")
        ab_path = base.with_suffix(".AB")
        sim_path = base.with_suffix(".sim")
        if not (ab_path.exists() and sim_path.exists()):
            continue
        prepared = prepare_melb_input(read_melb_input(case.input_path))
        ab = read_ab_dump(ab_path, case.block_count)
        simplex = read_simplex_dump(sim_path)
        generated_simplex = read_simplex_bytes(prepared.simplex_bytes)
        rows.append(
            {
                "d_code": case.d_code,
                "name": case.relative_name,
                "ab_max_diff": float(np.max(np.abs(prepared.ab.matrix - ab.matrix))),
                "sim_max_diff": float(np.max(np.abs(generated_simplex.values - simplex.values))),
            }
        )

    groups: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[int(row["d_code"])].append(row)

    for d_code, group_rows in sorted(groups.items()):
        print(
            "d_code",
            d_code,
            "n",
            len(group_rows),
            "ab<=1e-5",
            sum(float(row["ab_max_diff"]) <= 1e-5 for row in group_rows),
            "sim<=1e-5",
            sum(float(row["sim_max_diff"]) <= 1e-5 for row in group_rows),
            "maxab",
            max(float(row["ab_max_diff"]) for row in group_rows),
            "maxsim",
            max(float(row["sim_max_diff"]) for row in group_rows),
        )

    print("worst d_code 0/3")
    for row in sorted(
        [row for row in rows if row["d_code"] in (0, 3)],
        key=lambda item: float(item["sim_max_diff"]),
        reverse=True,
    )[:8]:
        print(row)


if __name__ == "__main__":
    main()
