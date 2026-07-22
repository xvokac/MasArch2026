from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "melb_regression"))

from melb_regression import (  # noqa: E402
    build_linprog_model,
    read_ab_dump,
    read_detail_txt,
    read_simplex_dump,
    solve_linprog_model,
)


ROOT = Path(r"D:\Documents\2026\MASARCH2026\masarch")
OUT = Path(r"C:\Users\Vokac\Documents\Codex\2026-07-10\jak\outputs\linprog_corpus_results.csv")


@dataclass(frozen=True)
class Candidate:
    base: Path
    txt: Path
    ab: Path
    sim: Path


def canonical_base(path: Path) -> Path:
    name = path.name
    lower = name.lower()
    for suffix in [".txt", ".ab", ".sim", ".out", "txt", "ab", "sim", "out"]:
        if lower.endswith(suffix):
            return path.with_name(name[: -len(suffix)])
    return path.with_suffix("")


def find_candidates(root: Path) -> list[Candidate]:
    by_base: dict[Path, dict[str, Path]] = {}
    for path in root.rglob("zlamal*"):
        if not path.is_file():
            continue
        lower = path.name.lower()
        kind = None
        for suffix, candidate_kind in [
            (".txt", "txt"),
            ("txt", "txt"),
            (".ab", "ab"),
            ("ab", "ab"),
            (".sim", "sim"),
            ("sim", "sim"),
        ]:
            if lower.endswith(suffix):
                kind = candidate_kind
                break
        if kind is None:
            continue
        by_base.setdefault(canonical_base(path), {})[kind] = path

    candidates = []
    for base, files in sorted(by_base.items()):
        if {"txt", "ab", "sim"} <= set(files):
            candidates.append(Candidate(base=base, txt=files["txt"], ab=files["ab"], sim=files["sim"]))
    return candidates


def run_case(candidate: Candidate) -> dict[str, object]:
    detail = read_detail_txt(candidate.txt)
    ab = read_ab_dump(candidate.ab, block_count=detail.block_count)
    simplex = read_simplex_dump(candidate.sim)
    model = build_linprog_model(detail, ab, simplex)
    result = solve_linprog_model(model)

    expected = detail.final_result_summary
    active = [index + 1 for index, value in enumerate(result.mechanism) if value > 1e-5]
    expected_active = [item.variable_index for item in expected.local_deformations]
    max_mechanism_diff = None
    if result.success and expected_active:
        max_mechanism_diff = max(
            abs(result.mechanism[item.variable_index - 1] - item.value)
            for item in expected.local_deformations
        )

    return {
        "base": str(candidate.base.relative_to(ROOT)),
        "success": result.success,
        "status": result.status,
        "message": result.message,
        "result_blocks": len(detail.result_summaries),
        "lambda_expected": expected.load_factor,
        "lambda_linprog": result.load_factor,
        "lambda_diff": result.load_factor - expected.load_factor if result.success else None,
        "active_expected": " ".join(map(str, expected_active)),
        "active_linprog": " ".join(map(str, active)),
        "active_match": active == expected_active,
        "max_mechanism_diff": max_mechanism_diff,
    }


def main() -> None:
    candidates = find_candidates(ROOT)
    print("candidates", len(candidates))
    rows: list[dict[str, object]] = []
    failures = 0
    mismatches = 0
    large_lambda = 0
    for candidate in candidates:
        try:
            row = run_case(candidate)
        except Exception as exc:  # noqa: BLE001
            row = {
                "base": str(candidate.base.relative_to(ROOT)),
                "success": False,
                "status": "exception",
                "message": repr(exc),
                "result_blocks": None,
                "lambda_expected": None,
                "lambda_linprog": None,
                "lambda_diff": None,
                "active_expected": "",
                "active_linprog": "",
                "active_match": False,
                "max_mechanism_diff": None,
            }
        rows.append(row)
        if not row["success"]:
            failures += 1
        if row["success"] and not row["active_match"]:
            mismatches += 1
        if row["success"] and row["lambda_diff"] is not None and abs(float(row["lambda_diff"])) > 1e-4:
            large_lambda += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("success", sum(1 for row in rows if row["success"]))
    print("failures", failures)
    print("active_mismatches", mismatches)
    print("lambda_diff_gt_1e-4", large_lambda)
    print("csv", OUT)
    print()
    print("first problematic rows")
    shown = 0
    for row in rows:
        bad = (not row["success"]) or (row["success"] and (not row["active_match"] or abs(float(row["lambda_diff"])) > 1e-4))
        if bad:
            print(row)
            shown += 1
            if shown >= 20:
                break


if __name__ == "__main__":
    main()
