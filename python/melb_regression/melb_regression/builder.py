from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import struct

import numpy as np

from .ab import ABDump
from .linprog_model import build_linprog_model_from_parts, solve_linprog_model
from .simplex import read_simplex_bytes


PI = 3.1415926535
D_PARA = 1e-4


@dataclass(frozen=True)
class PointLoad:
    x: float
    force: float
    width: float


@dataclass(frozen=True)
class MelbInput:
    path: Path
    span: float
    rise: float
    geom_code: int
    thickness: float
    masonry_unit_weight: float
    sliding_coefficient: float
    block_count: int
    point_loads: tuple[PointLoad, ...]
    fill_height: float
    fill_unit_weight: float
    q_code: int
    fill_spread_angle: float
    k_fill: tuple[float, float, float, float, float]
    d_code: int
    d_sigma: float
    interaction_file: str


@dataclass(frozen=True)
class MelbPrepared:
    input: MelbInput
    intrados_extrados: np.ndarray
    masonry_weights: np.ndarray
    fill_weights: np.ndarray
    external_loads: np.ndarray
    local_coordinates: np.ndarray
    transformed_masonry: np.ndarray
    transformed_fill: np.ndarray
    transformed_external: np.ndarray
    ab: ABDump
    simplex_bytes: bytes


@dataclass(frozen=True)
class IterationStep:
    index: int
    load_factor: float
    mechanism: np.ndarray
    normal_forces: np.ndarray
    normal_distances: np.ndarray
    shear_forces: np.ndarray
    d_crush: np.ndarray | None
    prepared: MelbPrepared


@dataclass(frozen=True)
class IterationResult:
    steps: tuple[IterationStep, ...]

    @property
    def final(self) -> IterationStep:
        return self.steps[-1]


class MelbSolveError(RuntimeError):
    def __init__(self, result, data: MelbInput):
        self.status = result.status
        self.solver_message = result.message
        super().__init__(_format_solve_error(result, data))


def read_melb_input(path: str | Path) -> MelbInput:
    input_path = Path(path)
    tokens = _numeric_input_tokens(input_path.read_text(encoding="cp1250", errors="ignore"))
    span = float(tokens[0])
    rise = float(tokens[1])
    geom_code = int(float(tokens[2]))
    thickness = float(tokens[3])
    masonry_unit_weight = float(tokens[4])
    sliding_coefficient = float(tokens[5])
    block_count = int(float(tokens[6]))
    force_count = int(float(tokens[7]))
    point_loads = tuple(
        PointLoad(float(tokens[8 + 3 * i]), float(tokens[9 + 3 * i]), float(tokens[10 + 3 * i]))
        for i in range(force_count)
    )
    index = 8 + 3 * force_count
    return MelbInput(
        path=input_path,
        span=span,
        rise=rise,
        geom_code=geom_code,
        thickness=thickness,
        masonry_unit_weight=masonry_unit_weight,
        sliding_coefficient=sliding_coefficient,
        block_count=block_count,
        point_loads=point_loads,
        fill_height=float(tokens[index]),
        fill_unit_weight=float(tokens[index + 1]),
        q_code=int(float(tokens[index + 2])),
        fill_spread_angle=float(tokens[index + 3]) * PI / 180.0,
        k_fill=tuple(float(tokens[index + 4 + i]) for i in range(5)),
        d_code=int(float(tokens[index + 9])),
        d_sigma=float(tokens[index + 10]),
        interaction_file=tokens[index + 11],
    )


def write_melb_input(data: MelbInput, path: str | Path, title: str | None = None) -> None:
    Path(path).write_text(format_melb_input(data, title=title), encoding="utf-8")


def format_melb_input(data: MelbInput, title: str | None = None) -> str:
    heading = title if title is not None else data.path.name
    lines = [
        heading,
        f"{_fmt_input(data.span)}                // span",
        f"{_fmt_input(data.rise)}                // rise",
        f"{int(data.geom_code)}                // geom_CODE 1=circle 2=parabola",
        f"{_fmt_input(data.thickness)}                // D",
        f"{_fmt_input(data.masonry_unit_weight)}                // gamma masonry",
        f"{_fmt_input(data.sliding_coefficient)}                // sliding coefficient",
        f"{int(data.block_count)}                // block count",
        f"{len(data.point_loads)}                // point load count",
    ]
    for load in data.point_loads:
        lines.append(
            f"{_fmt_input(load.x)} {_fmt_input(load.force)} {_fmt_input(load.width)}"
            "                // x force width"
        )
    lines.extend(
        [
            f"{_fmt_input(data.fill_height)}                // fill height",
            f"{_fmt_input(data.fill_unit_weight)}                // fill unit weight",
            (
                f"{int(data.q_code)} {_fmt_input(data.fill_spread_angle * 180.0 / PI)}"
                "                // Q_CODE fill spread angle [deg]"
            ),
            " ".join(_fmt_input(value) for value in data.k_fill)
            + "                // K_CODE K0 Ka Kp K_CODE_q",
            (
                f"{int(data.d_code)} {_fmt_input(data.d_sigma)} {data.interaction_file}"
                "                // d_CODE d_sigma interaction"
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def prepare_melb_input(data: MelbInput) -> MelbPrepared:
    intrados, extrados = _geometry(data)
    centers, dead_load = _dead_load(data.masonry_unit_weight, intrados, extrados)
    fill_load = _fill_load(data.fill_unit_weight, extrados, data.fill_height, data.thickness, data.rise)
    acting_points, live_load = _live_load(data, extrados)
    local = _geom_polar(intrados, extrados)
    if data.d_code == 3:
        local = local.copy()
        local[:, 0] /= 3.0
    p2 = _block_loads(intrados, extrados, centers, dead_load)
    fill2 = _fill2(intrados, extrados, data.k_fill, fill_load)
    q2 = _block_loads(intrados, extrados, acting_points, live_load)
    if data.k_fill[0] != 0.0 and data.k_fill[4] == 1.0:
        q2 = _modif_q2(q2, local, data.k_fill)
    ab_matrix = build_ab_matrix(local, data.sliding_coefficient)
    ab = ABDump(path=Path("<generated>"), block_count=data.block_count, matrix=ab_matrix)
    simplex_bytes = build_simplex_bytes(ab_matrix, data.sliding_coefficient, p2, q2, fill2)
    return MelbPrepared(
        input=data,
        intrados_extrados=np.column_stack([intrados, extrados]),
        masonry_weights=np.column_stack([centers, dead_load]),
        fill_weights=fill_load,
        external_loads=np.column_stack([acting_points, live_load]),
        local_coordinates=local,
        transformed_masonry=p2,
        transformed_fill=fill2,
        transformed_external=q2,
        ab=ab,
        simplex_bytes=simplex_bytes,
    )


def solve_melb_iterations(data: MelbInput, tolerance: float = 1e-2, max_iterations: int = 50) -> IterationResult:
    prepared = prepare_melb_input(data)
    initial = _solve_prepared_step(data, prepared, None, index=0)
    steps = [initial]
    if data.k_fill[0] == 2.0:
        prepared = _prepared_with_lateral_soil_pressure(data, prepared, initial.mechanism)
        corrected = _solve_prepared_step(data, prepared, None, index=1)
        steps.append(corrected)
        initial = corrected
    if data.d_code not in (1, 2, 4):
        return IterationResult(tuple(steps))

    d_crush = _calculate_d_crush(data, initial.normal_forces, initial.normal_distances)
    previous_load_factor = initial.load_factor
    start_index = steps[-1].index + 1
    for index in range(start_index, start_index + max_iterations):
        local = _modified_local_coordinates(prepared.local_coordinates, d_crush, data.d_code)
        ab_matrix = build_ab_matrix(local, data.sliding_coefficient)
        simplex_bytes = build_simplex_bytes(
            ab_matrix,
            data.sliding_coefficient,
            prepared.transformed_masonry,
            prepared.transformed_external,
            prepared.transformed_fill,
        )
        ab = ABDump(path=Path("<generated-iterated>"), block_count=data.block_count, matrix=ab_matrix)
        iterated = MelbPrepared(
            input=data,
            intrados_extrados=prepared.intrados_extrados,
            masonry_weights=prepared.masonry_weights,
            fill_weights=prepared.fill_weights,
            external_loads=prepared.external_loads,
            local_coordinates=local,
            transformed_masonry=prepared.transformed_masonry,
            transformed_fill=prepared.transformed_fill,
            transformed_external=prepared.transformed_external,
            ab=ab,
            simplex_bytes=simplex_bytes,
        )
        step = _solve_prepared_step(data, iterated, d_crush, index=index)
        steps.append(step)
        if abs(previous_load_factor - step.load_factor) <= tolerance:
            break
        previous_load_factor = step.load_factor
        d_crush = _calculate_d_crush(data, step.normal_forces, step.normal_distances)
    return IterationResult(tuple(steps))


def build_ab_matrix(local_coordinates: np.ndarray, sliding_coefficient: float) -> np.ndarray:
    local = local_coordinates
    block_count = len(local) - 1
    rows = 4 * (block_count + 1) if sliding_coefficient > 0.0 else 2 * (block_count + 1)
    matrix = np.zeros((rows, 3 * (block_count + 1)), dtype=np.float32)
    row = 0
    for k in range(block_count + 1):
        for sign in (1.0, -1.0):
            for j in range(block_count + 1):
                x = 0.0
                y = 0.0
                if k <= j:
                    x += local[k, 0] * math.sin(local[k, 1])
                    y += local[k, 0] * math.cos(local[k, 1])
                if k < j:
                    for i in range(k, j):
                        x += sign * local[i, 2] * math.sin(local[i, 3])
                        y += sign * local[i, 2] * math.cos(local[i, 3])
                matrix[row, 3 * j : 3 * j + 3] = (x, y, 1.0 if sign > 0.0 and k <= j else -1.0 if k <= j else 0.0)
            row += 1
    if sliding_coefficient > 0.0:
        for k in range(block_count + 1):
            for sign in (1.0, -1.0):
                for j in range(block_count + 1):
                    if k <= j:
                        if sign > 0.0:
                            values = (
                                math.cos(local[k, 1]) + sliding_coefficient * math.sin(local[k, 1]),
                                -math.sin(local[k, 1]) + sliding_coefficient * math.cos(local[k, 1]),
                                0.0,
                            )
                        else:
                            values = (
                                -math.cos(local[k, 1]) + sliding_coefficient * math.sin(local[k, 1]),
                                math.sin(local[k, 1]) + sliding_coefficient * math.cos(local[k, 1]),
                                0.0,
                            )
                        matrix[row, 3 * j : 3 * j + 3] = values
                row += 1
    return matrix


def build_simplex_bytes(
    ab_matrix: np.ndarray,
    sliding_coefficient: float,
    masonry_loads: np.ndarray,
    variable_loads: np.ndarray,
    fill_loads: np.ndarray,
) -> bytes:
    variable_count = 4 * len(masonry_loads) if sliding_coefficient > 0.0 else 2 * len(masonry_loads)
    chunks = [struct.pack("<3i", variable_count, 4, -1)]
    permanent = masonry_loads + fill_loads
    objective = -(ab_matrix @ permanent.ravel())
    norm = ab_matrix @ variable_loads.ravel()
    chunks.append(_pack_floats(objective))
    chunks.append(_pack_floats(norm))
    chunks.append(struct.pack("<f", 1.0))
    chunks.append(struct.pack("<i", 3))
    for component in range(3):
        chunks.append(_pack_floats(_nplus1_constraint(ab_matrix, component)))
        chunks.append(struct.pack("<f", 0.0))
        chunks.append(struct.pack("<i", 3))
    return b"".join(chunks)


def _solve_prepared_step(
    data: MelbInput,
    prepared: MelbPrepared,
    d_crush: np.ndarray | None,
    index: int,
) -> IterationStep:
    simplex = read_simplex_bytes(prepared.simplex_bytes)
    model = build_linprog_model_from_parts(
        joint_count=data.block_count + 1,
        ab=prepared.ab,
        simplex=simplex,
        d_code=data.d_code if d_crush is not None else 0,
        d_sigma=data.d_sigma,
        d_crush=d_crush,
    )
    result = solve_linprog_model(model)
    if not result.success:
        raise MelbSolveError(result, data)
    slacks = model.inequality_rhs - model.inequality_matrix @ result.variables
    normal_forces, normal_distances = _normal_force_result(
        data,
        prepared.local_coordinates,
        slacks,
        d_crush,
    )
    return IterationStep(
        index=index,
        load_factor=result.load_factor,
        mechanism=result.mechanism,
        normal_forces=normal_forces,
        normal_distances=normal_distances,
        shear_forces=_shear_force_result(data, slacks),
        d_crush=d_crush,
        prepared=prepared,
    )


def _format_solve_error(result, data: MelbInput) -> str:
    context = (
        f"Soubor: {data.path.name}\n"
        f"Parametry: N={data.block_count}, geom_CODE={data.geom_code}, "
        f"Q_CODE={data.q_code}, K_CODE={data.k_fill[0]:.0f}, d_CODE={data.d_code}\n"
        f"Stav solveru: {result.status}\n"
        f"HiGHS: {result.message}"
    )
    if result.status == 3:
        return (
            "Vypocet se zamkl: linearni program je neomezeny (unbounded).\n\n"
            "To obvykle znamena, ze zadani pripousti mechanismus bez konecneho "
            "nasobku zatizeni, nebo chybi nektere omezujici vazby. Zkontrolujte "
            "zejmena geometrii, pocet bloku, smer a polohu zatizeni, klouzani s_b "
            "a zvolenou pevnostni metodu d_CODE.\n\n"
            + context
        )
    if result.status == 2:
        return (
            "Linearni program nema pripustne reseni (infeasible).\n\n"
            "Zadane podminky si navzajem odporuji nebo jsou prilis omezujici. "
            "Zkontrolujte geometrii, zatizeni, zemni tlak a pevnostni parametry.\n\n"
            + context
        )
    if result.status == 4:
        return (
            "Solver narazil na numericky problem.\n\n"
            "Zkuste zkontrolovat meritko vstupnich hodnot, velmi male nebo velmi "
            "velke parametry a pripadne zjednodusit zadani.\n\n"
            + context
        )
    return "Vypocet selhal pri reseni linearniho programu.\n\n" + context


def _prepared_with_lateral_soil_pressure(
    data: MelbInput,
    prepared: MelbPrepared,
    mechanism: np.ndarray,
) -> MelbPrepared:
    fill2, q2 = _modif_lateral_soil_pressure(data, prepared, mechanism)
    simplex_bytes = build_simplex_bytes(
        prepared.ab.matrix,
        data.sliding_coefficient,
        prepared.transformed_masonry,
        q2,
        fill2,
    )
    return MelbPrepared(
        input=data,
        intrados_extrados=prepared.intrados_extrados,
        masonry_weights=prepared.masonry_weights,
        fill_weights=prepared.fill_weights,
        external_loads=prepared.external_loads,
        local_coordinates=prepared.local_coordinates,
        transformed_masonry=prepared.transformed_masonry,
        transformed_fill=fill2,
        transformed_external=q2,
        ab=prepared.ab,
        simplex_bytes=simplex_bytes,
    )


def _modif_lateral_soil_pressure(
    data: MelbInput,
    prepared: MelbPrepared,
    mechanism: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    block_count = data.block_count
    local = prepared.local_coordinates
    ab_matrix = prepared.ab.matrix
    fill2 = prepared.transformed_fill.copy()
    q2 = prepared.transformed_external.copy()
    deformation = np.zeros((block_count, 3), dtype=float)
    for block_index in range(block_count):
        for component in range(3):
            column = 3 * block_index + component
            deformation[block_index, component] = ab_matrix[:, column] @ mechanism

    epsilon = 1e-3
    extrados_displacement = np.zeros((block_count, 3), dtype=float)
    for i in range(1, block_count + 1):
        row = i - 1
        extrados_displacement[row, 0] = (
            deformation[row, 0] * epsilon
            + local[row, 0] * math.cos(local[row, 1] - deformation[row, 2] * epsilon)
            - local[row, 0] * math.cos(local[row, 1])
        )
        extrados_displacement[row, 1] = (
            deformation[row, 0] * epsilon
            + local[row, 2] * math.cos(local[row, 3] - deformation[row, 2] * epsilon)
            - local[row, 2] * math.cos(local[row, 3])
            + local[i, 0] * math.cos(local[i, 1] - deformation[row, 2] * epsilon)
            - local[i, 0] * math.cos(local[i, 1])
        )
        extrados_displacement[row, 2] = 0.5 * (
            extrados_displacement[row, 0] + extrados_displacement[row, 1]
        ) * _signum(-math.sin(local[row, 3]))

    max_displacement = 0.0
    for i in range(block_count):
        direction = _signum(-math.sin(local[i, 3]))
        max_displacement = max(
            max_displacement,
            extrados_displacement[i, 0] * direction,
            extrados_displacement[i, 1] * direction,
        )

    for i in range(1, block_count + 1):
        row = i - 1
        y_force = _force_y_from_local_moment(fill2[row], local[row])
        fill2[row, 2] -= fill2[row, 0] * y_force
        fill2[row, 0] = _scaled_lateral_force(fill2[row, 0], extrados_displacement[row, 2], max_displacement, data.k_fill)
        fill2[row, 2] += fill2[row, 0] * y_force

        if data.k_fill[4] == 1.0 and q2[row, 1] != 0.0:
            y_force = _force_y_from_local_moment(q2[row], local[row])
            q2[row, 2] -= q2[row, 0] * y_force
            q2[row, 0] = _scaled_lateral_force(q2[row, 0], extrados_displacement[row, 2], max_displacement, data.k_fill)
            q2[row, 2] += q2[row, 0] * y_force
    return fill2, q2


def _force_y_from_local_moment(load: np.ndarray, local_row: np.ndarray) -> float:
    denominator = local_row[2] * (load[1] * math.cos(local_row[3]) + load[0] * math.sin(local_row[3]))
    if abs(denominator) == 0.0:
        return 0.0
    n_value = (
        load[2]
        - local_row[0] * (load[1] * math.cos(local_row[1]) + load[0] * math.sin(local_row[1]))
    ) / denominator
    return local_row[0] * math.sin(local_row[1]) + n_value * local_row[2] * math.sin(local_row[3])


def _scaled_lateral_force(force: float, displacement: float, max_displacement: float, k_fill: tuple[float, ...]) -> float:
    if displacement <= 0.0:
        return force * k_fill[2] / k_fill[1]
    if displacement > 0.0 and max_displacement != 0.0:
        return force * (k_fill[1] + (k_fill[3] - k_fill[1]) / max_displacement * displacement) / k_fill[1]
    return force


def _normal_force_result(
    data: MelbInput,
    local_coordinates: np.ndarray,
    slacks: np.ndarray,
    d_crush: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    mint = slacks[0 : 2 * (data.block_count + 1) : 2].copy()
    mext = slacks[1 : 2 * (data.block_count + 1) : 2].copy()
    if data.d_code == 2 and d_crush is not None:
        dissipated_work = 0.5 * data.d_sigma * np.square(d_crush)
        mint -= dissipated_work
        mext -= dissipated_work
    depth = 2.0 * local_coordinates[:, 0]
    total = mint + mext
    normal_forces = total / depth
    normal_distances = np.divide(
        mext * depth,
        total,
        out=np.zeros_like(total),
        where=np.abs(total) > 0.0,
    ) + (data.thickness / 2.0 - local_coordinates[:, 0])
    return normal_forces, normal_distances


def _shear_force_result(data: MelbInput, slacks: np.ndarray) -> np.ndarray:
    joint_count = data.block_count + 1
    if data.sliding_coefficient <= 0.0 or len(slacks) < 4 * joint_count:
        return np.zeros(joint_count, dtype=float)
    u_plus = slacks[2 * joint_count : 4 * joint_count : 2]
    u_minus = slacks[2 * joint_count + 1 : 4 * joint_count : 2]
    return (u_plus - u_minus) / 2.0


def _calculate_d_crush(data: MelbInput, normal_forces: np.ndarray, normal_distances: np.ndarray) -> np.ndarray:
    if data.d_code in (1, 2):
        return normal_forces / data.d_sigma
    if data.d_code == 4:
        return _calculate_interaction_d_crush(data, normal_forces, normal_distances)
    raise ValueError(f"d_CODE={data.d_code} is not iterative")


def _modified_local_coordinates(local_coordinates: np.ndarray, d_crush: np.ndarray, d_code: int) -> np.ndarray:
    modified = local_coordinates.copy()
    if d_code in (1, 2):
        modified[:, 0] = local_coordinates[:, 0] - d_crush / 2.0 * d_code
    elif d_code == 4:
        modified[:, 0] = local_coordinates[:, 0] - d_crush
    else:
        raise ValueError(f"d_CODE={d_code} is not iterative")
    return modified


def _calculate_interaction_d_crush(
    data: MelbInput,
    normal_forces: np.ndarray,
    normal_distances: np.ndarray,
) -> np.ndarray:
    diagram_path = data.path.with_name(data.interaction_file)
    if not diagram_path.exists():
        diagram_path = data.path.parent.parent / data.interaction_file
    normal_axis, moment_axis, normal_max = _read_interaction_diagram(diagram_path)
    values = np.zeros_like(normal_forces)
    for index, normal_force in enumerate(normal_forces):
        if normal_force >= normal_max:
            raise ValueError("normal force exceeds interaction diagram")
        segment = -10
        for j in range(len(normal_axis) - 1):
            if normal_axis[j] <= normal_force < normal_axis[j + 1]:
                segment = j - 1
        if segment == -10:
            raise ValueError("normal force interval not found in interaction diagram")
        segment = max(0, min(segment, len(normal_axis) - 4))
        max_moment = _polint(normal_axis[segment : segment + 4], moment_axis[segment : segment + 4], normal_force)
        values[index] = data.thickness / 2.0 - max_moment / normal_force
    return values


def _read_interaction_diagram(path: Path) -> tuple[np.ndarray, np.ndarray, float]:
    lines = path.read_text(encoding="cp1250", errors="ignore").splitlines()
    tokens = " ".join(line.split("//", 1)[0] for line in lines[1:]).split()
    count = int(float(tokens[0]))
    normal_max = float(tokens[1])
    values = np.array([float(token) for token in tokens[2:]], dtype=float).reshape((count + 1, 2))
    return values[:, 0], values[:, 1], normal_max


def _polint(x_values: np.ndarray, y_values: np.ndarray, x: float) -> float:
    result = 0.0
    for i, x_i in enumerate(x_values):
        term = y_values[i]
        for j, x_j in enumerate(x_values):
            if i != j:
                term *= (x - x_j) / (x_i - x_j)
        result += term
    return float(result)


def _numeric_input_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for line in text.splitlines()[1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("["):
            continue
        if "//" in stripped:
            stripped = stripped.split("//", 1)[0]
        tokens.extend(stripped.split())
    if len(tokens) < 20:
        raise ValueError("input file does not contain enough MELB fields")
    return tokens


def _fmt_input(value: float) -> str:
    return f"{float(value):.12g}"


def _geometry(data: MelbInput) -> tuple[np.ndarray, np.ndarray]:
    if data.geom_code == 1:
        return _geom1(data.span, data.rise, data.thickness, data.block_count)
    if data.geom_code == 2:
        return _geom2(data.span, data.rise, data.thickness, data.block_count)
    raise ValueError(f"unsupported geom_code: {data.geom_code}")


def _geom1(span: float, rise: float, thickness: float, block_count: int) -> tuple[np.ndarray, np.ndarray]:
    radius = span * span / 8.0 / rise + rise / 2.0
    fin = 2.0 / block_count * math.asin(span / 2.0 / radius)
    intrados = np.zeros((block_count + 1, 2), dtype=float)
    extrados = np.zeros((block_count + 1, 2), dtype=float)
    for i in range(block_count + 1):
        intrados[i] = (radius * math.cos(i * fin), -radius * math.sin(i * fin))
        extrados[i] = ((radius + thickness) * math.cos(i * fin), -(radius + thickness) * math.sin(i * fin))
    origin_i = intrados[0].copy()
    origin_e = origin_i.copy()
    intrados -= origin_i
    extrados -= origin_e
    angle = (PI - block_count * fin) / 2.0 + PI
    return _rotate(intrados, angle), _rotate(extrados, angle)


def _geom2(span: float, rise: float, thickness: float, block_count: int) -> tuple[np.ndarray, np.ndarray]:
    a = -rise * 4.0 / span / span
    b = rise * 4.0 / span
    pom = math.sqrt(span * span + 16.0 * rise * rise)
    arc_length = 0.5 * pom + span * span / 8.0 / rise * math.log(4.0 * rise / span + pom / span)
    intrados = np.zeros((block_count + 1, 2), dtype=float)
    accumulated = 0.0
    x = 0.0
    for i in range(1, block_count + 1):
        target = i / block_count * arc_length
        while accumulated < target:
            y0 = a * x * x + b * x
            x1 = x + D_PARA
            y1 = a * x1 * x1 + b * x1
            accumulated += math.sqrt(D_PARA * D_PARA + (y1 - y0) * (y1 - y0))
            x = x1
        intrados[i, 0] = x
    intrados[:, 1] = a * intrados[:, 0] * intrados[:, 0] + b * intrados[:, 0]
    extrados = np.zeros_like(intrados)
    for i in range(block_count + 1):
        normal_angle = math.atan(2.0 * a * intrados[i, 0] + b) + PI / 2.0
        extrados[i, 0] = intrados[i, 0] + thickness * math.cos(normal_angle)
        extrados[i, 1] = intrados[i, 1] + thickness * math.sin(normal_angle)
    return intrados, extrados


def _rotate(points: np.ndarray, angle: float) -> np.ndarray:
    rotated = np.zeros_like(points)
    rotated[:, 0] = points[:, 0] * math.cos(angle) + points[:, 1] * math.sin(angle)
    rotated[:, 1] = -points[:, 0] * math.sin(angle) + points[:, 1] * math.cos(angle)
    return rotated


def _dead_load(unit_weight: float, intrados: np.ndarray, extrados: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    count = len(intrados) - 1
    centers = np.zeros((count, 2), dtype=float)
    loads = np.zeros(count, dtype=float)
    for i in range(1, count + 1):
        a1, a2, a3, a4 = _block_signed_areas(i, intrados, extrados)
        area = a1 + a2 + a3 + a4
        loads[i - 1] = unit_weight * area
        centers[i - 1, 0] = (
            a1 * (intrados[i - 1, 0] + intrados[i, 0]) / 3.0
            + a2 * (intrados[i, 0] + extrados[i, 0]) / 3.0
            + a3 * (extrados[i, 0] + extrados[i - 1, 0]) / 3.0
            + a4 * (extrados[i - 1, 0] + intrados[i - 1, 0]) / 3.0
        ) / area
        centers[i - 1, 1] = (
            a1 * (intrados[i - 1, 1] + intrados[i, 1]) / 3.0
            + a2 * (intrados[i, 1] + extrados[i, 1]) / 3.0
            + a3 * (extrados[i, 1] + extrados[i - 1, 1]) / 3.0
            + a4 * (extrados[i - 1, 1] + intrados[i - 1, 1]) / 3.0
        ) / area
    return centers, loads


def _block_signed_areas(i: int, intrados: np.ndarray, extrados: np.ndarray) -> tuple[float, float, float, float]:
    return (
        0.5 * (intrados[i - 1, 0] * intrados[i, 1] - intrados[i, 0] * intrados[i - 1, 1]),
        0.5 * (intrados[i, 0] * extrados[i, 1] - extrados[i, 0] * intrados[i, 1]),
        0.5 * (extrados[i, 0] * extrados[i - 1, 1] - extrados[i - 1, 0] * extrados[i, 1]),
        0.5 * (extrados[i - 1, 0] * intrados[i - 1, 1] - intrados[i - 1, 0] * extrados[i - 1, 1]),
    )


def _fill_load(unit_weight: float, extrados: np.ndarray, fill_height: float, thickness: float, rise: float) -> np.ndarray:
    count = len(extrados) - 1
    fill = np.zeros((count, 4), dtype=float)
    nivel = rise + thickness + fill_height
    for i in range(1, count + 1):
        a1 = 0.5 * (extrados[i - 1, 0] * extrados[i, 1] - extrados[i, 0] * extrados[i - 1, 1])
        a2 = 0.5 * (extrados[i, 0] * nivel - extrados[i, 0] * extrados[i, 1])
        a3 = 0.5 * (extrados[i, 0] * nivel - extrados[i - 1, 0] * nivel)
        a4 = 0.5 * (extrados[i - 1, 0] * extrados[i - 1, 1] - extrados[i - 1, 0] * nivel)
        area = a1 + a2 + a3 + a4
        x = (
            a1 * (extrados[i - 1, 0] + extrados[i, 0]) / 3.0
            + a2 * (extrados[i, 0] + extrados[i, 0]) / 3.0
            + a3 * (extrados[i, 0] + extrados[i - 1, 0]) / 3.0
            + a4 * (extrados[i - 1, 0] + extrados[i - 1, 0]) / 3.0
        ) / area
        t = (extrados[i - 1, 0] - x) / (extrados[i - 1, 0] - extrados[i, 0])
        y = extrados[i - 1, 1] - t * (extrados[i - 1, 1] - extrados[i, 1])
        fill[i - 1] = (unit_weight * area, -extrados[i - 1, 1] + extrados[i, 1], x, y)
    return fill


def _live_load(data: MelbInput, extrados: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if data.q_code == 0:
        return _live_load_q0(data, extrados)
    if data.q_code == 1:
        return _live_load_q1(data, extrados)
    if data.q_code == 2:
        return _live_load_q2(data, extrados)
    raise ValueError(f"unsupported Q_CODE: {data.q_code}")


def _live_load_q0(data: MelbInput, extrados: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    count = data.block_count
    acting = np.zeros((count, 2), dtype=float)
    loads = np.zeros(count, dtype=float)
    for i in range(1, count + 1):
        acting[i - 1] = extrados[i - 1]
        for load in data.point_loads:
            if extrados[i - 1, 0] <= load.x < extrados[i, 0]:
                new_load = loads[i - 1] + load.force
                acting[i - 1, 0] = (loads[i - 1] * acting[i - 1, 0] + load.force * load.x) / new_load
                if acting[i - 1, 0] == extrados[i - 1, 0]:
                    acting[i - 1, 1] = extrados[i - 1, 1]
                else:
                    acting[i - 1, 1] = extrados[i - 1, 1] + (extrados[i, 1] - extrados[i - 1, 1]) * (
                        extrados[i, 0] - extrados[i - 1, 0]
                    ) / (acting[i - 1, 0] - extrados[i - 1, 0])
                loads[i - 1] = new_load
    return acting, loads


def _live_load_q1(data: MelbInput, extrados: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    count = data.block_count
    acting = extrados[:-1].copy()
    loads = np.zeros(count, dtype=float)
    nivel = data.rise + data.thickness + data.fill_height
    for load in data.point_loads:
        if load.x < extrados[0, 0] or load.x >= extrados[-1, 0]:
            raise ValueError("Q_CODE=1 requires external loads above the arch")
        if load.width == 0.0 and data.fill_spread_angle == 0.0:
            raise ValueError("Q_CODE=1 needs non-zero load width or spreading angle")
        spread_width = None
        for j in range(1, count + 1):
            if extrados[j - 1, 0] <= load.x < extrados[j, 0]:
                t_param = (load.x - extrados[j - 1, 0]) / (extrados[j, 0] - extrados[j - 1, 0])
                surface_y = t_param * (extrados[j, 1] - extrados[j - 1, 1]) + extrados[j - 1, 1]
                spread_width = 2.0 * (nivel - surface_y) * math.tan(data.fill_spread_angle) + load.width
                break
        if spread_width is None:
            raise ValueError("load position was not found on extrados")
        intensity = load.force / spread_width
        left = load.x - spread_width / 2.0
        right = load.x + spread_width / 2.0
        for j in range(1, count + 1):
            start = extrados[j - 1, 0]
            end = extrados[j, 0]
            overlap_left = max(left, start)
            overlap_right = min(right, end)
            if overlap_left >= overlap_right:
                continue
            force = intensity * (overlap_right - overlap_left)
            centroid_x = 0.5 * (overlap_left + overlap_right)
            row = j - 1
            acting[row, 0] = (loads[row] * acting[row, 0] + force * centroid_x) / (loads[row] + force)
            acting[row, 1] = _interpolate_extrados_y(acting[row, 0], extrados[row], extrados[row + 1])
            loads[row] += force
    return acting, loads


def _live_load_q2(data: MelbInput, extrados: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    count = data.block_count
    acting = extrados[:-1].copy()
    loads = np.zeros(count, dtype=float)
    bouss = np.zeros((count, 5), dtype=float)
    nivel = data.rise + data.thickness + data.fill_height
    integration_count = 100
    for load in data.point_loads:
        bouss1 = np.zeros((count, 5), dtype=float)
        lhs = 0.0
        rhs = 0.0
        for j in range(1, count + 1):
            for t in range(5):
                x = t / 4.0 * (extrados[j, 0] - extrados[j - 1, 0]) + extrados[j - 1, 0]
                y = t / 4.0 * (extrados[j, 1] - extrados[j - 1, 1]) + extrados[j - 1, 1]
                horizontal_distance = abs(load.x - x)
                depth = nivel - y
                if depth == 0.0:
                    raise ValueError("Boussinesq load spreading has zero depth")
                beta = math.atan((horizontal_distance - 0.5 * load.width) / depth)
                if beta <= data.fill_spread_angle:
                    alfa = math.atan((horizontal_distance + 0.5 * load.width) / depth) - beta
                    bouss1[j - 1, t] = 1.0 / PI * (alfa + math.sin(alfa) * math.cos(alfa + 2.0 * beta))
                    if j == 1 and t == 0 and beta < data.fill_spread_angle:
                        lhs = -1.0
                    if j == count and t == 4 and beta < data.fill_spread_angle:
                        rhs = -1.0
        if lhs != 0.0:
            lhs = 0.0
            depth = nivel
            x0 = load.x - 0.5 * load.width - nivel * math.tan(data.fill_spread_angle)
            for j in range(integration_count + 1):
                x = x0 + j * 1.0 / integration_count * (extrados[0, 0] - x0)
                horizontal_distance = abs(load.x - x)
                beta = math.atan((horizontal_distance - 0.5 * load.width) / depth)
                alfa = math.atan((horizontal_distance + 0.5 * load.width) / depth) - beta
                weight = 1 if j in (0, integration_count) else 2
                lhs += weight * 1.0 / PI * (alfa + math.sin(alfa) * math.cos(alfa + 2.0 * beta))
            lhs *= 0.5 * (extrados[0, 0] - x0) / integration_count
        if rhs != 0.0:
            rhs = 0.0
            depth = nivel
            x0 = load.x + 0.5 * load.width + nivel * math.tan(data.fill_spread_angle)
            for j in range(integration_count + 1):
                # The original C code uses integer division here (`j/nb`).
                x = x0 - (j // integration_count) * (x0 - extrados[-1, 0])
                horizontal_distance = abs(load.x - x)
                beta = math.atan((horizontal_distance - 0.5 * load.width) / depth)
                alfa = math.atan((horizontal_distance + 0.5 * load.width) / depth) - beta
                weight = 1 if j in (0, integration_count) else 2
                rhs += weight * 1.0 / PI * (alfa + math.sin(alfa) * math.cos(alfa + 2.0 * beta))
            rhs *= 0.5 * (x0 - extrados[-1, 0]) / integration_count

        integral = 0.0
        for j in range(1, count + 1):
            projection = extrados[j, 0] - extrados[j - 1, 0]
            integral += projection / 4.0 * (
                0.5 * bouss1[j - 1, 0]
                + bouss1[j - 1, 1]
                + bouss1[j - 1, 2]
                + bouss1[j - 1, 3]
                + 0.5 * bouss1[j - 1, 4]
            )
        multiplier = load.force / (integral + lhs + rhs)
        bouss = bouss1 * multiplier

    for i in range(1, count + 1):
        projection = extrados[i, 0] - extrados[i - 1, 0]
        force = projection / 4.0 * (
            0.5 * bouss[i - 1, 0]
            + bouss[i - 1, 1]
            + bouss[i - 1, 2]
            + bouss[i - 1, 3]
            + 0.5 * bouss[i - 1, 4]
        )
        moment = 0.0
        for t in range(4):
            segment_moment = (
                ((t * projection / 4.0) + extrados[i - 1, 0]) * bouss[i - 1, t]
                + (((t + 1) * projection / 4.0) + extrados[i - 1, 0]) * bouss[i - 1, t + 1]
            ) * 0.5
            moment += projection / 4.0 * segment_moment
        if force != 0.0:
            row = i - 1
            acting[row, 0] = (loads[row] * acting[row, 0] + moment) / (loads[row] + force)
            acting[row, 1] = _interpolate_extrados_y(acting[row, 0], extrados[row], extrados[row + 1])
            loads[row] += force
    return acting, loads


def _interpolate_extrados_y(x: float, start: np.ndarray, end: np.ndarray) -> float:
    if x - start[0] == 0.0:
        return float(start[1])
    return float(start[1] + (end[1] - start[1]) * (end[0] - start[0]) / (x - start[0]))


def _geom_polar(intrados: np.ndarray, extrados: np.ndarray) -> np.ndarray:
    count = len(intrados) - 1
    local = np.zeros((count + 1, 4), dtype=float)
    mid = 0.5 * (intrados + extrados)
    for i in range(count + 1):
        local[i, 0] = _distance(intrados[i], extrados[i]) / 2.0
        local[i, 1] = _angle(intrados[i], extrados[i])
        if i != count:
            local[i, 2] = _distance(mid[i], mid[i + 1])
            local[i, 3] = _angle(mid[i], mid[i + 1])
        else:
            local[i, 2] = 1.0
            local[i, 3] = local[i, 1] - PI / 2.0
    return local


def _block_loads(intrados: np.ndarray, extrados: np.ndarray, points: np.ndarray, loads: np.ndarray) -> np.ndarray:
    count = len(loads)
    result = np.zeros((count + 1, 3), dtype=float)
    for i in range(1, count + 1):
        result[i - 1, 1] = loads[i - 1]
        result[i - 1, 2] = (points[i - 1, 0] - 0.5 * (intrados[i - 1, 0] + extrados[i - 1, 0])) * loads[i - 1]
    return result


def _fill2(intrados: np.ndarray, extrados: np.ndarray, k_fill: tuple[float, ...], fill_load: np.ndarray) -> np.ndarray:
    count = len(fill_load)
    result = np.zeros((count + 1, 3), dtype=float)
    for i in range(1, count + 1):
        if k_fill[0] == 0.0:
            result[i - 1, 0] = 0.0
        else:
            result[i - 1, 0] = fill_load[i - 1, 0] * fill_load[i - 1, 1] * k_fill[1]
        result[i - 1, 1] = fill_load[i - 1, 0]
        result[i - 1, 2] = (
            result[i - 1, 1] * (fill_load[i - 1, 2] - 0.5 * (intrados[i - 1, 0] + extrados[i - 1, 0]))
            + result[i - 1, 0] * (fill_load[i - 1, 3] - 0.5 * (intrados[i - 1, 1] + extrados[i - 1, 1]))
        )
    return result


def _modif_q2(q2: np.ndarray, local: np.ndarray, k_fill: tuple[float, ...]) -> np.ndarray:
    modified = q2.copy()
    for i in range(1, len(q2)):
        if modified[i - 1, 1] != 0.0:
            x_force = modified[i - 1, 2] / modified[i - 1, 1]
            n = (x_force - local[i - 1, 0] * math.cos(local[i - 1, 1])) / (
                local[i - 1, 2] * math.cos(local[i - 1, 3])
            )
            y_force = local[i - 1, 0] * math.sin(local[i - 1, 1]) + n * local[i - 1, 2] * math.sin(local[i - 1, 3])
            modified[i - 1, 0] = modified[i - 1, 1] * k_fill[1] * local[i - 1, 2] * math.cos(local[i - 1, 3]) * _signum(local[i - 1, 3])
            modified[i - 1, 2] = modified[i - 1, 2] + modified[i - 1, 0] * y_force
    return modified


def _nplus1_constraint(ab_matrix: np.ndarray, component: int) -> np.ndarray:
    joint_count = ab_matrix.shape[1] // 3
    return ab_matrix[:, 3 * (joint_count - 1) + component]


def _distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(math.hypot(b[0] - a[0], b[1] - a[1]))


def _angle(a: np.ndarray, b: np.ndarray) -> float:
    return float(math.atan2(b[1] - a[1], b[0] - a[0]))


def _signum(value: float) -> float:
    if value < 0.0:
        return -1.0
    if value > 0.0:
        return 1.0
    return 0.0


def _pack_floats(values: np.ndarray) -> bytes:
    packed = np.asarray(values, dtype=np.float32)
    return struct.pack("<" + "f" * len(packed), *packed)
