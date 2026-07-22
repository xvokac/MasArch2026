from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np

from .corpus import LocalDeformation


@dataclass(frozen=True)
class ResultSummary:
    icase: int
    load_factor: float
    block_count: int
    local_deformations: tuple[LocalDeformation, ...]


@dataclass(frozen=True)
class DetailResult:
    icase: int
    load_factor: float
    block_count: int
    local_deformations: tuple[LocalDeformation, ...]
    joint_indices: np.ndarray
    normal_forces: np.ndarray
    normal_distances: np.ndarray
    shear_forces: np.ndarray
    crush_distances: np.ndarray | None = None


@dataclass(frozen=True)
class MelbDetail:
    path: Path
    input_name: str
    d_code: int
    d_sigma: float
    intrados_extrados: np.ndarray
    masonry_weights: np.ndarray
    fill_weights: np.ndarray
    external_loads: np.ndarray
    local_coordinates: np.ndarray
    transformed_masonry: np.ndarray
    transformed_fill: np.ndarray
    transformed_external: np.ndarray
    result: DetailResult
    result_summaries: tuple[ResultSummary, ...]
    d_crush_vectors: tuple[np.ndarray, ...]

    @property
    def block_count(self) -> int:
        return int(self.result.block_count)

    @property
    def joint_count(self) -> int:
        return self.block_count + 1

    @property
    def final_result_summary(self) -> ResultSummary:
        return self.result_summaries[-1]


def read_detail_txt(path: str | Path) -> MelbDetail:
    detail_path = Path(path)
    text = detail_path.read_text(encoding="cp1250", errors="ignore")
    input_match = re.search(r"^Vstupni soubor:\s*(.+?)\s*$", text, re.MULTILINE)
    if input_match is None:
        raise ValueError(f"{detail_path} does not look like a MELB detail output")

    summaries = _parse_result_summaries(text)
    result = _parse_result(text, summaries[0])
    d_code, d_sigma = _parse_input_method(text)
    return MelbDetail(
        path=detail_path,
        input_name=input_match.group(1),
        d_code=d_code,
        d_sigma=d_sigma,
        intrados_extrados=_parse_table(text, "Ortoganalni souradnice intrados a extrados:", 4),
        masonry_weights=_parse_table(text, "Vlastni tiha klenby - jednotlive bloky:", 3),
        fill_weights=_parse_table(text, "Tiha nadnasypu pusobici na bloky:", 4),
        external_loads=_parse_table(text, "Vnejsi zatizeni pusobici na bloky:", 3),
        local_coordinates=_parse_table(text, "Ortogonalni lokalni souradnice jednotlivych bloku:", 4),
        transformed_masonry=_parse_table(text, "Transformovane zatizeni vlastni tihou klenby:", 3),
        transformed_fill=_parse_table(text, "Transformovane zatizeni nadnasypem:", 3),
        transformed_external=_parse_table(text, "Transformovane zatizeni vnejsich sil:", 3),
        result=result,
        result_summaries=summaries,
        d_crush_vectors=_parse_vectors_after(text, "Vektor d_crush:"),
    )


def _parse_table(text: str, title: str, columns: int) -> np.ndarray:
    lines = text.splitlines()
    try:
        start = lines.index(title)
    except ValueError as exc:
        raise ValueError(f"section not found: {title}") from exc

    rows: list[list[float]] = []
    for line in lines[start + 2 :]:
        values = _parse_numeric_line(line)
        if len(values) != columns:
            break
        rows.append(values)
    if not rows:
        raise ValueError(f"section has no numeric rows: {title}")
    return np.array(rows, dtype=float)


def _parse_result(text: str, summary: ResultSummary) -> DetailResult:
    return DetailResult(
        icase=summary.icase,
        load_factor=summary.load_factor,
        block_count=summary.block_count,
        local_deformations=summary.local_deformations,
        joint_indices=_parse_vector_after(text, "Vektor indexu spary mezi bloky:"),
        normal_forces=_parse_vector_after(text, "Vektor normalovych sil ve sparach"),
        normal_distances=_parse_vector_after(text, "Vektor vzdalenosti N od hornoho povrchu klenby:"),
        shear_forces=_parse_vector_after(text, "Vektor posouvajicich sil ve sparach:"),
        crush_distances=_parse_optional_vector_after(text, "Vektor d_crush:"),
    )


def _parse_result_summaries(text: str) -> tuple[ResultSummary, ...]:
    summaries: list[ResultSummary] = []
    pattern = re.compile(
        r"icase\s*=\s*([-+]?\d+).*?"
        r"lambda\s*=\s*([-+]?\d+(?:\.\d+)?).*?"
        r"pocet bloku N\s*=\s*(\d+).*?"
        r"Vektor lokalnich deformaci:\s*(.*?)"
        r"(?=\n\s*Vektor indexu spary mezi bloky:)",
        re.S,
    )
    for match in pattern.finditer(text):
        summaries.append(
            ResultSummary(
                icase=int(match.group(1)),
                load_factor=float(match.group(2)),
                block_count=int(match.group(3)),
                local_deformations=_parse_local_deformations(match.group(4)),
            )
        )
    if not summaries:
        raise ValueError("detail result block is incomplete")
    return tuple(summaries)


def _parse_vector_after(text: str, marker: str) -> np.ndarray:
    vector = _parse_optional_vector_after(text, marker)
    if vector is None:
        raise ValueError(f"vector not found: {marker}")
    return vector


def _parse_optional_vector_after(text: str, marker: str) -> np.ndarray | None:
    start = text.find(marker)
    if start < 0:
        return None
    tail = text[start + len(marker) :].splitlines()[1:]
    numbers: list[float] = []
    for line in tail:
        values = _parse_numeric_line(line)
        if not values:
            if numbers:
                break
            continue
        numbers.extend(values)
        if len(values) < 3:
            break
    return np.array(numbers, dtype=float) if numbers else None


def _parse_vectors_after(text: str, marker: str) -> tuple[np.ndarray, ...]:
    vectors: list[np.ndarray] = []
    start = 0
    while True:
        index = text.find(marker, start)
        if index < 0:
            break
        tail = text[index + len(marker) :].splitlines()[1:]
        numbers: list[float] = []
        for line in tail:
            values = _parse_numeric_line(line)
            if not values:
                if numbers:
                    break
                continue
            numbers.extend(values)
            if len(values) < 3:
                break
        if numbers:
            vectors.append(np.array(numbers, dtype=float))
        start = index + len(marker)
    return tuple(vectors)


def _parse_input_method(text: str) -> tuple[int, float]:
    head = text.split("Ortoganalni souradnice intrados a extrados:", 1)[0]
    data_lines = []
    for line in head.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("Vstupni soubor:") or stripped.startswith("***"):
            continue
        if stripped.startswith("["):
            break
        data_lines.append(stripped)
    tokens = " ".join(data_lines).split()
    if len(tokens) < 20:
        return 0, 0.0
    force_count = int(float(tokens[7]))
    index = 8 + 3 * force_count
    return int(float(tokens[index + 9])), float(tokens[index + 10])


def _parse_local_deformations(text: str) -> tuple[LocalDeformation, ...]:
    values: list[LocalDeformation] = []
    pattern = re.compile(
        r"^\s*(\d+):\s+fi\s+(\d+)\s+(int|ext)\s*=\s*([-+]?\d+(?:\.\d+)?)",
        re.MULTILINE,
    )
    for match in pattern.finditer(text):
        values.append(
            LocalDeformation(
                variable_index=int(match.group(1)),
                joint_index=int(match.group(2)),
                side=match.group(3),
                value=float(match.group(4)),
            )
        )
    return tuple(values)


def _parse_numeric_line(line: str) -> list[float]:
    stripped = line.strip()
    if not stripped:
        return []
    parts = stripped.split()
    values: list[float] = []
    for part in parts:
        try:
            values.append(float(part))
        except ValueError:
            return []
    return values
