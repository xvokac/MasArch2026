from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import read_detail_txt, read_melb_input, read_simplex_bytes, read_simplex_dump, solve_melb_iterations  # noqa: E402
from melb_regression.detail import _parse_numeric_line  # noqa: E402


ROOT = Path(r"D:\Documents\2026\MASARCH2026\Melbourne")


def table_without_header(text: str, title: str) -> np.ndarray:
    lines = text.splitlines()
    start = lines.index(title)
    rows = []
    for line in lines[start + 1 :]:
        values = _parse_numeric_line(line)
        if not values:
            if rows:
                break
            continue
        rows.append(values)
    return np.array(rows, dtype=float)


def main() -> None:
    data = read_melb_input(ROOT / "TEST.IN")
    result = solve_melb_iterations(data)
    detail = read_detail_txt(ROOT / "test.txt")
    text = (ROOT / "test.txt").read_text(encoding="cp1250", errors="ignore")
    new_fill = table_without_header(text, "Nove transformovane zatizeni nadnasypem:")
    new_external = table_without_header(text, "Nove transformovane zatizeni vnejsich sil:")
    simplex = read_simplex_dump(ROOT / "test.sim")
    generated_simplex = read_simplex_bytes(result.final.prepared.simplex_bytes)
    print("loads generated", [step.load_factor for step in result.steps])
    print("loads expected ", [summary.load_factor for summary in detail.result_summaries])
    print("final lambda diff", result.final.load_factor - detail.final_result_summary.load_factor)
    print("new fill diff", np.max(np.abs(result.final.prepared.transformed_fill[: len(new_fill)] - new_fill)))
    print(
        "new external diff",
        np.max(np.abs(result.final.prepared.transformed_external[: len(new_external)] - new_external)),
    )
    print("final sim diff", np.max(np.abs(generated_simplex.values - simplex.values)))


if __name__ == "__main__":
    main()
