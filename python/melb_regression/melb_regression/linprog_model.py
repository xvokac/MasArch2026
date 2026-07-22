from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

from .ab import ABDump
from .detail import MelbDetail
from .simplex import SimplexDump


@dataclass(frozen=True)
class LinprogModel:
    objective: np.ndarray
    inequality_matrix: np.ndarray
    inequality_rhs: np.ndarray


@dataclass(frozen=True)
class LinprogResult:
    load_factor: float
    variables: np.ndarray
    mechanism: np.ndarray
    success: bool
    status: int
    message: str


def build_linprog_model(detail: MelbDetail, ab: ABDump, simplex: SimplexDump) -> LinprogModel:
    d_crush = None
    if detail.d_code == 2 and detail.d_crush_vectors:
        vector_index = max(0, len(detail.result_summaries) - 2)
        d_crush = detail.d_crush_vectors[min(vector_index, len(detail.d_crush_vectors) - 1)]
    return build_linprog_model_from_parts(
        joint_count=detail.joint_count,
        ab=ab,
        simplex=simplex,
        d_code=detail.d_code,
        d_sigma=detail.d_sigma,
        d_crush=d_crush,
    )


def build_linprog_model_from_parts(
    joint_count: int,
    ab: ABDump,
    simplex: SimplexDump,
    d_code: int = 0,
    d_sigma: float = 0.0,
    d_crush: np.ndarray | None = None,
) -> LinprogModel:
    if joint_count != ab.joint_count:
        raise ValueError("joint count and AB joint counts do not match")
    variable_count = 4 * joint_count
    if simplex.nr_variable_count != variable_count:
        raise ValueError("simplex variable count does not match joint count")

    blocks = simplex.streamed_blocks
    if len(blocks) < 5:
        raise ValueError("simplex dump does not contain enough streamed blocks")
    right_hand_side = blocks[0].copy()
    if d_code == 2:
        _apply_crisfield_packham_dissipation(joint_count, d_sigma, d_crush, right_hand_side)
    load_coefficients = blocks[1]
    tableau = simplex.nr_tableau
    compatibility = np.vstack(
        [
            _shifted_coefficients(tableau[2], 0, variable_count),
            _shifted_coefficients(tableau[3], 1, variable_count),
            _shifted_coefficients(tableau[4], 2, variable_count),
        ]
    )
    return LinprogModel(
        objective=np.array([-1.0, 0.0, 0.0, 0.0], dtype=float),
        inequality_matrix=np.column_stack([load_coefficients, compatibility.T]),
        inequality_rhs=right_hand_side,
    )


def _shifted_coefficients(row: np.ndarray, offset: int, count: int) -> np.ndarray:
    coefficients = np.zeros(count, dtype=float)
    available = max(0, min(count, len(row) - offset))
    if available:
        coefficients[:available] = row[offset : offset + available]
    return coefficients


def _apply_crisfield_packham_dissipation(
    joint_count: int,
    d_sigma: float,
    d_crush: np.ndarray | None,
    right_hand_side: np.ndarray,
) -> None:
    if d_crush is None:
        raise ValueError("d_CODE=2 model needs a d_crush vector")
    if len(d_crush) != joint_count:
        raise ValueError("d_crush vector length does not match detail joint count")
    dissipated_work = 0.5 * d_sigma * np.square(d_crush)
    for joint_index, value in enumerate(dissipated_work):
        right_hand_side[2 * joint_index] += value
        right_hand_side[2 * joint_index + 1] += value


def solve_linprog_model(model: LinprogModel) -> LinprogResult:
    result = linprog(
        model.objective,
        A_ub=model.inequality_matrix,
        b_ub=model.inequality_rhs,
        bounds=[(None, None)] * len(model.objective),
        method="highs",
    )
    load_factor = float(result.x[0]) if result.success else float("nan")
    variables = result.x if result.success else np.array([], dtype=float)
    mechanism = -result.ineqlin.marginals if result.success else np.array([], dtype=float)
    return LinprogResult(
        load_factor=load_factor,
        variables=variables,
        mechanism=mechanism,
        success=bool(result.success),
        status=int(result.status),
        message=str(result.message),
    )
