from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class MelbResult:
    output_path: Path
    icase: int
    load_factor: float
    local_deformations: tuple["LocalDeformation", ...]


@dataclass(frozen=True)
class LocalDeformation:
    variable_index: int
    joint_index: int
    side: str
    value: float


@dataclass(frozen=True)
class MelbCase:
    input_path: Path
    relative_name: str
    span: float
    rise: float
    geom_code: int
    thickness: float
    masonry_unit_weight: float
    sliding_coefficient: float
    block_count: int
    force_count: int
    fill_height: float
    fill_unit_weight: float
    q_code: int
    q_angle: float
    k_code: int
    k0: float
    ka: float
    kp: float
    k_code_q: int
    d_code: int
    d_sigma: float
    interaction_file: str
    result: MelbResult | None


def load_zlamal_cases(root: str | Path) -> list[MelbCase]:
    base = Path(root)
    cases = [_parse_case(path, base) for path in sorted(base.rglob("zlamal*.in"))]
    return [case for case in cases if case is not None]


def _parse_case(path: Path, base: Path) -> MelbCase | None:
    tokens = path.read_text(encoding="cp1250", errors="ignore").split()
    if len(tokens) < 20:
        return None
    try:
        span = float(tokens[0])
        rise = float(tokens[1])
        geom_code = int(float(tokens[2]))
        thickness = float(tokens[3])
        masonry_unit_weight = float(tokens[4])
        sliding_coefficient = float(tokens[5])
        block_count = int(float(tokens[6]))
        force_count = int(float(tokens[7]))
        index = 8 + 3 * force_count
        fill_height = float(tokens[index])
        fill_unit_weight = float(tokens[index + 1])
        q_code = int(float(tokens[index + 2]))
        q_angle = float(tokens[index + 3])
        k_code = int(float(tokens[index + 4]))
        k0 = float(tokens[index + 5])
        ka = float(tokens[index + 6])
        kp = float(tokens[index + 7])
        k_code_q = int(float(tokens[index + 8]))
        d_code = int(float(tokens[index + 9]))
        d_sigma = float(tokens[index + 10])
        interaction_file = tokens[index + 11]
    except (IndexError, ValueError):
        return None

    return MelbCase(
        input_path=path,
        relative_name=str(path.relative_to(base)),
        span=span,
        rise=rise,
        geom_code=geom_code,
        thickness=thickness,
        masonry_unit_weight=masonry_unit_weight,
        sliding_coefficient=sliding_coefficient,
        block_count=block_count,
        force_count=force_count,
        fill_height=fill_height,
        fill_unit_weight=fill_unit_weight,
        q_code=q_code,
        q_angle=q_angle,
        k_code=k_code,
        k0=k0,
        ka=ka,
        kp=kp,
        k_code_q=k_code_q,
        d_code=d_code,
        d_sigma=d_sigma,
        interaction_file=interaction_file,
        result=_parse_result(path),
    )


def _parse_result(input_path: Path) -> MelbResult | None:
    candidates = [
        input_path.with_suffix(".out"),
        input_path.with_name(input_path.stem + "out"),
    ]
    output_path = next((candidate for candidate in candidates if candidate.exists()), None)
    if output_path is None:
        return None
    text = output_path.read_text(encoding="cp1250", errors="ignore")
    icase_match = re.search(r"icase\s*=\s*([-+]?\d+)", text)
    lambda_match = re.search(r"lambda\s*=\s*([-+]?\d+(?:\.\d+)?)", text)
    if icase_match is None or lambda_match is None:
        return None
    return MelbResult(
        output_path=output_path,
        icase=int(icase_match.group(1)),
        load_factor=float(lambda_match.group(1)),
        local_deformations=_parse_local_deformations(text),
    )


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
