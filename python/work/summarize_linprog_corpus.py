from __future__ import annotations

from collections import defaultdict
import csv
from pathlib import Path


path = Path(r"C:\Users\Vokac\Documents\Codex\2026-07-10\jak\outputs\linprog_corpus_results.csv")
rows = list(csv.DictReader(path.open(encoding="utf-8")))
groups: dict[str, list[dict[str, str]]] = defaultdict(list)
for row in rows:
    groups[row["base"].split("\\")[0]].append(row)

for group, group_rows in sorted(groups.items()):
    diffs = [
        abs(float(row["lambda_diff"]))
        for row in group_rows
        if row["success"] == "True" and row["lambda_diff"]
    ]
    print(
        group,
        "n",
        len(group_rows),
        "active",
        sum(row["active_match"] == "True" for row in group_rows),
        "<=1e-4",
        sum(diff <= 1e-4 for diff in diffs),
        "<=1e-3",
        sum(diff <= 1e-3 for diff in diffs),
        "<=1e-2",
        sum(diff <= 1e-2 for diff in diffs),
        "maxdiff",
        max(diffs) if diffs else None,
    )
