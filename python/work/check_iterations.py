from __future__ import annotations

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

import numpy as np

from melb_regression import (  # noqa: E402
    load_zlamal_cases,
    read_ab_dump,
    read_detail_txt,
    read_melb_input,
    read_simplex_bytes,
    read_simplex_dump,
    solve_melb_iterations,
)


ROOT = Path(r"D:\Documents\2026\MASARCH2026\masarch")


def main() -> None:
    for name in [r"zlamal1\zlamal1_1", r"zlamal2\zlamal2_1", r"zlamal3\zlamal3_1"]:
        base = ROOT / name
        result = solve_melb_iterations(read_melb_input(base.with_suffix(".in")))
        detail = read_detail_txt(base.with_suffix(".txt"))
        print(name)
        print("  generated", [round(step.load_factor, 6) for step in result.steps])
        print("  expected ", [round(summary.load_factor, 6) for summary in detail.result_summaries])
        ab = read_ab_dump(base.with_suffix(".AB"), block_count=result.final.prepared.input.block_count)
        simplex = read_simplex_dump(base.with_suffix(".sim"))
        generated_simplex = read_simplex_bytes(result.final.prepared.simplex_bytes)
        print("  final AB diff ", float(np.max(np.abs(result.final.prepared.ab.matrix - ab.matrix))))
        print("  final sim diff", float(np.max(np.abs(generated_simplex.values - simplex.values))))

    print("corpus")
    rows = []
    for case in load_zlamal_cases(ROOT):
        if case.d_code not in (1, 2, 4):
            continue
        detail_path = case.input_path.with_suffix(".txt")
        if not detail_path.exists():
            continue
        detail = read_detail_txt(detail_path)
        result = solve_melb_iterations(read_melb_input(case.input_path))
        rows.append(
            {
                "name": case.relative_name,
                "d_code": case.d_code,
                "steps": len(result.steps),
                "expected_steps": len(detail.result_summaries),
                "diff": result.final.load_factor - detail.final_result_summary.load_factor,
            }
        )
    for d_code in (1, 2, 4):
        group = [row for row in rows if row["d_code"] == d_code]
        diffs = [abs(float(row["diff"])) for row in group]
        print(
            "d_code",
            d_code,
            "n",
            len(group),
            "steps_match",
            sum(row["steps"] == row["expected_steps"] for row in group),
            "<=1e-4",
            sum(diff <= 1e-4 for diff in diffs),
            "<=1e-3",
            sum(diff <= 1e-3 for diff in diffs),
            "maxdiff",
            max(diffs) if diffs else None,
        )
    print("worst")
    for row in sorted(rows, key=lambda item: abs(float(item["diff"])), reverse=True)[:12]:
        print(row)
    print("step mismatches")
    for row in rows:
        if row["steps"] != row["expected_steps"]:
            print(row)


if __name__ == "__main__":
    main()
