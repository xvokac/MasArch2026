from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import sys

import numpy as np
from scipy.optimize import linprog


def _melb_root() -> Path:
    return Path(__file__).resolve().parents[2] / "melb_regression"


try:
    from melb_regression.melb_regression import MelbInput, MelbPrepared, PointLoad, prepare_melb_input, read_melb_input
    from melb_regression.melb_regression import builder as melb_builder
except ImportError:
    try:
        from melb_regression import MelbInput, MelbPrepared, PointLoad, prepare_melb_input, read_melb_input
        from melb_regression import builder as melb_builder
    except ImportError:
        melb_root = _melb_root()
        if melb_root.exists():
            sys.path.insert(0, str(melb_root))
        from melb_regression import MelbInput, MelbPrepared, PointLoad, prepare_melb_input, read_melb_input
        import melb_regression.builder as melb_builder


PI = 3.1415926535


@dataclass(frozen=True)
class ArchLBTInput:
    path: Path
    span: float
    rise: float
    geom_code: int
    extrados_mode: str
    thickness: float
    arch_width: float
    masonry_unit_weight: float
    block_count: int
    point_loads: tuple[PointLoad, ...]
    fill_height: float
    fill_unit_weight: float
    q_code: int
    fill_spread_angle: float
    friction_coefficient: float
    compression_strength: float


@dataclass(frozen=True)
class LoadSummary:
    permanent_vertical: float
    fill_vertical: float
    variable_vertical: float
    total_vertical: float


@dataclass(frozen=True)
class StaticState:
    """Internal resultants assembled from one arch end.

    Columns are interpreted as shear T, normal force N, and bending moment M in
    the local transformed-load convention inherited from MELB preparation.
    """

    shear_forces: np.ndarray
    normal_forces: np.ndarray
    moments: np.ndarray


@dataclass(frozen=True)
class LinearStaticModel:
    normal_constant: np.ndarray
    normal_coefficients: np.ndarray
    moment_constant: np.ndarray
    moment_coefficients: np.ndarray
    shear_constant: np.ndarray
    shear_coefficients: np.ndarray


@dataclass(frozen=True)
class GlobalLoads:
    forces: np.ndarray
    points: np.ndarray
    block_indices: np.ndarray


@dataclass(frozen=True)
class LowerBoundResult:
    success: bool
    status: int
    message: str
    load_factor: float
    governing_joint: int | None
    reaction_x: float
    reaction_y: float
    reaction_moment: float
    permanent_state: StaticState
    variable_state: StaticState
    final_state: StaticState


@dataclass(frozen=True)
class InteractionDiagram:
    normal_forces: np.ndarray
    moments: np.ndarray


@dataclass(frozen=True)
class EquilibriumDiagnostic:
    success: bool
    message: str
    variable_count: int
    joint_count: int
    finite_values: bool
    sample_state: StaticState


@dataclass(frozen=True)
class ConstraintDiagnostic:
    name: str
    success: bool
    status: int
    message: str
    load_factor: float
    reaction_x: float
    reaction_y: float
    reaction_moment: float
    governing_joint: int | None
    final_state: StaticState


@dataclass(frozen=True)
class EquilibriumCheck:
    origin_x: float
    origin_y: float
    load_force_x: float
    load_force_y: float
    load_moment: float
    left_reaction_x: float
    left_reaction_y: float
    left_reaction_moment: float
    right_reaction_x: float
    right_reaction_y: float
    right_reaction_moment: float
    residual_force_x: float
    residual_force_y: float
    residual_moment: float


@dataclass(frozen=True)
class ArchLBTModel:
    input: MelbInput
    arch_width: float
    extrados_mode: str
    prepared: MelbPrepared
    load_summary: LoadSummary

    @property
    def block_count(self) -> int:
        return self.input.block_count

    @property
    def joint_count(self) -> int:
        return self.input.block_count + 1

    @property
    def intrados(self) -> np.ndarray:
        return self.prepared.intrados_extrados[:, 0:2]

    @property
    def extrados(self) -> np.ndarray:
        return self.prepared.intrados_extrados[:, 2:4]

    @property
    def section_depths(self) -> np.ndarray:
        return np.linalg.norm(self.extrados - self.intrados, axis=1)


def read_arch_lbt_input(path: str | Path) -> ArchLBTInput:
    input_path = Path(path)
    values: dict[str, str] = {}
    point_loads: list[PointLoad] = []
    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = _strip_lbt_comment(raw_line).strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"Invalid ArchLBT input line without '=': {raw_line}")
        key, raw_value = line.split("=", 1)
        key = key.strip().lower()
        raw_value = raw_value.strip()
        if key == "point_load":
            parts = raw_value.replace(",", " ").split()
            if len(parts) != 3:
                raise ValueError("point_load must contain x, force and width")
            point_loads.append(PointLoad(float(parts[0]), float(parts[1]), float(parts[2])))
        else:
            values[key] = raw_value

    def required_float(key: str) -> float:
        if key not in values:
            raise ValueError(f"Missing ArchLBT input value: {key}")
        return float(values[key])

    def required_int(key: str) -> int:
        if key not in values:
            raise ValueError(f"Missing ArchLBT input value: {key}")
        return int(float(values[key]))

    angle = values.get("fill_spread_angle_deg", values.get("fill_spread_angle", "0.0"))
    return ArchLBTInput(
        path=input_path,
        span=required_float("span"),
        rise=required_float("rise"),
        geom_code=required_int("geom_code"),
        extrados_mode=values.get("extrados_mode", "normal").strip().lower(),
        thickness=required_float("thickness"),
        arch_width=float(values.get("arch_width", "1.0")),
        masonry_unit_weight=required_float("masonry_unit_weight"),
        block_count=required_int("block_count"),
        point_loads=tuple(point_loads),
        fill_height=required_float("fill_height"),
        fill_unit_weight=required_float("fill_unit_weight"),
        q_code=required_int("q_code"),
        fill_spread_angle=float(angle) * PI / 180.0,
        friction_coefficient=required_float("friction_coefficient"),
        compression_strength=required_float("compression_strength"),
    )


def write_arch_lbt_input(data: ArchLBTInput, path: str | Path) -> None:
    Path(path).write_text(format_arch_lbt_input(data), encoding="utf-8")


def format_arch_lbt_input(data: ArchLBTInput) -> str:
    lines = [
        "# ArchLBT input",
        "# Unit convention: use one consistent force-length system.",
        "# Geometry is in length units, typical m. Unit weights are force/volume, typical kN/m3.",
        "# Surface point_load force F is the total force on the loaded length, typical kN.",
        "# Self-weight and fill loads are multiplied internally by arch_width; point_load F is not.",
        f"span = {_fmt_lbt(data.span)}",
        f"rise = {_fmt_lbt(data.rise)}",
        f"geom_code = {int(data.geom_code)}",
        "# extrados_mode: normal, horizontal, horizontal_width_radial_joints.",
        f"extrados_mode = {data.extrados_mode}",
        f"thickness = {_fmt_lbt(data.thickness)}",
        "# arch_width is the out-of-plane width b of the analysed arch strip.",
        f"arch_width = {_fmt_lbt(data.arch_width)}",
        f"masonry_unit_weight = {_fmt_lbt(data.masonry_unit_weight)}",
        f"block_count = {int(data.block_count)}",
    ]
    for load in data.point_loads:
        lines.append(f"point_load = {_fmt_lbt(load.x)} {_fmt_lbt(load.force)} {_fmt_lbt(load.width)}")
    lines.extend(
        [
            f"fill_height = {_fmt_lbt(data.fill_height)}",
            f"fill_unit_weight = {_fmt_lbt(data.fill_unit_weight)}",
            f"q_code = {int(data.q_code)}",
            f"fill_spread_angle_deg = {_fmt_lbt(data.fill_spread_angle * 180.0 / PI)}",
            f"friction_coefficient = {_fmt_lbt(data.friction_coefficient)}",
            f"compression_strength = {_fmt_lbt(data.compression_strength)}",
            "",
        ]
    )
    return "\n".join(lines)


def lbt_input_from_melb(data: MelbInput, *, friction_coefficient: float | None = None, path: Path | None = None) -> ArchLBTInput:
    return ArchLBTInput(
        path=data.path if path is None else path,
        span=data.span,
        rise=data.rise,
        geom_code=data.geom_code,
        extrados_mode="normal",
        thickness=data.thickness,
        arch_width=1.0,
        masonry_unit_weight=data.masonry_unit_weight,
        block_count=data.block_count,
        point_loads=data.point_loads,
        fill_height=data.fill_height,
        fill_unit_weight=data.fill_unit_weight,
        q_code=data.q_code,
        fill_spread_angle=data.fill_spread_angle,
        friction_coefficient=data.sliding_coefficient if friction_coefficient is None else friction_coefficient,
        compression_strength=data.d_sigma,
    )


def melb_input_from_lbt(data: ArchLBTInput) -> MelbInput:
    return MelbInput(
        path=data.path,
        span=data.span,
        rise=data.rise,
        geom_code=data.geom_code,
        thickness=data.thickness,
        masonry_unit_weight=data.masonry_unit_weight,
        sliding_coefficient=data.friction_coefficient,
        block_count=data.block_count,
        point_loads=data.point_loads,
        fill_height=data.fill_height,
        fill_unit_weight=data.fill_unit_weight,
        q_code=data.q_code,
        fill_spread_angle=data.fill_spread_angle,
        k_fill=(0.0, 0.0, 0.0, 0.0, 0.0),
        d_code=0,
        d_sigma=data.compression_strength,
        interaction_file="",
    )


def read_model(path: str | Path) -> ArchLBTModel:
    input_path = Path(path)
    if _looks_like_lbt_input(input_path):
        return build_model(read_arch_lbt_input(input_path))
    return build_model(read_melb_input(input_path))


def build_model(data: MelbInput | ArchLBTInput) -> ArchLBTModel:
    arch_width = data.arch_width if isinstance(data, ArchLBTInput) else 1.0
    extrados_mode = data.extrados_mode if isinstance(data, ArchLBTInput) else "normal"
    melb_data = melb_input_from_lbt(data) if isinstance(data, ArchLBTInput) else data
    prepared = prepare_arch_lbt_input(data, melb_data) if isinstance(data, ArchLBTInput) else prepare_melb_input(melb_data)
    return ArchLBTModel(
        input=melb_data,
        arch_width=arch_width,
        extrados_mode=extrados_mode,
        prepared=prepared,
        load_summary=summarize_loads(prepared, arch_width),
    )


def prepare_arch_lbt_input(data: ArchLBTInput, melb_data: MelbInput) -> MelbPrepared:
    mode = data.extrados_mode.lower()
    if mode in ("normal", "offset", "constant"):
        return prepare_melb_input(melb_data)
    if mode not in ("horizontal", "horizontal_width_radial_joints"):
        raise ValueError(f"unsupported extrados_mode: {data.extrados_mode}")

    intrados, standard_extrados = melb_builder._geometry(melb_data)
    extrados = horizontal_extrados(data, intrados, standard_extrados)
    if np.any(extrados[:, 1] <= intrados[:, 1]):
        raise ValueError("horizontal extrados must be above the intrados in every joint")

    centers, dead_load = melb_builder._dead_load(melb_data.masonry_unit_weight, intrados, extrados)
    fill_load = melb_builder._fill_load(
        melb_data.fill_unit_weight,
        extrados,
        melb_data.fill_height,
        melb_data.thickness,
        melb_data.rise,
    )
    acting_points, live_load = melb_builder._live_load(melb_data, extrados)
    local = melb_builder._geom_polar(intrados, extrados)
    p2 = melb_builder._block_loads(intrados, extrados, centers, dead_load)
    fill2 = melb_builder._fill2(intrados, extrados, melb_data.k_fill, fill_load)
    q2 = melb_builder._block_loads(intrados, extrados, acting_points, live_load)
    if melb_data.k_fill[0] != 0.0 and melb_data.k_fill[4] == 1.0:
        q2 = melb_builder._modif_q2(q2, local, melb_data.k_fill)
    ab_matrix = melb_builder.build_ab_matrix(local, melb_data.sliding_coefficient)
    ab = melb_builder.ABDump(path=Path("<generated-horizontal-extrados>"), block_count=melb_data.block_count, matrix=ab_matrix)
    simplex_bytes = melb_builder.build_simplex_bytes(ab_matrix, melb_data.sliding_coefficient, p2, q2, fill2)
    return MelbPrepared(
        input=melb_data,
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


def horizontal_extrados(data: ArchLBTInput, intrados: np.ndarray, standard_extrados: np.ndarray) -> np.ndarray:
    top_y = data.rise + data.thickness
    mode = data.extrados_mode.lower()
    if mode == "horizontal":
        return np.column_stack([intrados[:, 0], np.full(len(intrados), top_y)])
    if mode == "horizontal_width_radial_joints":
        normal_vectors = standard_extrados - intrados
        normal_lengths = np.linalg.norm(normal_vectors, axis=1)
        unit_normals = np.divide(normal_vectors, normal_lengths[:, None], out=np.zeros_like(normal_vectors), where=normal_lengths[:, None] > 0.0)
        if np.any(unit_normals[:, 1] <= 1e-12):
            raise ValueError("horizontal_width_radial_joints requires upward normal directions")
        factors = (top_y - intrados[:, 1]) / unit_normals[:, 1]
        extrados = intrados + factors[:, None] * unit_normals
        if np.any(np.diff(extrados[:, 0]) <= 0.0):
            raise ValueError("horizontal_width_radial_joints requires increasing extrados x coordinates")
        return extrados
    raise ValueError(f"unsupported extrados_mode: {data.extrados_mode}")


def _looks_like_lbt_input(path: Path) -> bool:
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = _strip_lbt_comment(raw_line).strip()
            if not line:
                continue
            return "=" in line
    except UnicodeDecodeError:
        return False
    return False


def _strip_lbt_comment(line: str) -> str:
    for marker in ("#", "//"):
        index = line.find(marker)
        if index >= 0:
            line = line[:index]
    return line


def _fmt_lbt(value: float) -> str:
    return f"{value:.12g}"


def summarize_loads(prepared: MelbPrepared, arch_width: float = 1.0) -> LoadSummary:
    permanent_vertical = float(np.sum(prepared.transformed_masonry[:, 1]) * arch_width)
    fill_vertical = float(np.sum(prepared.transformed_fill[:, 1]) * arch_width)
    variable_vertical = float(np.sum(prepared.transformed_external[:, 1]))
    return LoadSummary(
        permanent_vertical=permanent_vertical,
        fill_vertical=fill_vertical,
        variable_vertical=variable_vertical,
        total_vertical=permanent_vertical + fill_vertical + variable_vertical,
    )


def solve_infinite_strength_lower_bound(model: ArchLBTModel) -> LowerBoundResult:
    """Maximize load factor using a statically admissible reaction family.

    Unknowns are left-end reaction components ``Rx``, ``Ry``, left-end moment
    ``M0``, and the load factor ``lambda``. For every joint, section resultants
    are linear functions of those four unknowns. The current strength domain is
    the infinite-compression no-tension block ``N >= 0`` and
    ``abs(M) <= N*D/2``.
    """

    linear_model = build_linear_static_model(model)
    solution = solve_linear_strength_lp(linear_model, model.input.thickness, include_normal=True, include_moment=True)
    if not solution.success:
        zero_variables = np.zeros(4, dtype=float)
        zero_state = evaluate_linear_static_model(linear_model, zero_variables)
        load_factor = math.inf if int(solution.status) == 3 else 0.0
        return LowerBoundResult(
            success=False,
            status=int(solution.status),
            message=str(solution.message),
            load_factor=load_factor,
            governing_joint=find_governing_joint(zero_state, model.input.thickness),
            reaction_x=0.0,
            reaction_y=0.0,
            reaction_moment=0.0,
            permanent_state=zero_state,
            variable_state=evaluate_linear_static_model(linear_model, np.array([0.0, 0.0, 0.0, 1.0])),
            final_state=zero_state,
        )
    rx, ry, m0, factor = solution.x
    final_state = evaluate_linear_static_model(linear_model, solution.x)
    governing_joint = find_governing_joint(final_state, model.input.thickness)
    return LowerBoundResult(
        success=True,
        status=int(solution.status),
        message=str(solution.message),
        load_factor=factor,
        governing_joint=governing_joint,
        reaction_x=rx,
        reaction_y=ry,
        reaction_moment=m0,
        permanent_state=evaluate_linear_static_model(linear_model, np.array([0.0, 0.0, 0.0, 0.0])),
        variable_state=evaluate_linear_static_model(linear_model, np.array([0.0, 0.0, 0.0, 1.0])),
        final_state=final_state,
    )


def solve_parabolic_interaction_lower_bound(
    model: ArchLBTModel,
    width: float | None = None,
    segment_count: int = 48,
    friction_coefficient: float | None = None,
) -> LowerBoundResult:
    interaction_width = model.arch_width if width is None else width
    friction = model.input.sliding_coefficient if friction_coefficient is None else friction_coefficient
    linear_model = build_linear_static_model(model)
    solution = solve_linear_interaction_lp(
        linear_model,
        fc=model.input.d_sigma,
        width=interaction_width,
        section_depths=model.section_depths,
        segment_count=segment_count,
        friction_coefficient=friction,
    )
    if not solution.success:
        zero_variables = np.zeros(4, dtype=float)
        zero_state = evaluate_linear_static_model(linear_model, zero_variables)
        load_factor = math.inf if int(solution.status) == 3 else 0.0
        return LowerBoundResult(
            success=False,
            status=int(solution.status),
            message=str(solution.message),
            load_factor=load_factor,
            governing_joint=find_governing_joint(zero_state, model.input.thickness),
            reaction_x=0.0,
            reaction_y=0.0,
            reaction_moment=0.0,
            permanent_state=zero_state,
            variable_state=evaluate_linear_static_model(linear_model, np.array([0.0, 0.0, 0.0, 1.0])),
            final_state=zero_state,
        )
    rx, ry, m0, factor = solution.x
    final_state = evaluate_linear_static_model(linear_model, solution.x)
    return LowerBoundResult(
        success=True,
        status=int(solution.status),
        message=str(solution.message),
        load_factor=float(factor),
        governing_joint=find_interaction_governing_joint(final_state, model.input.d_sigma, interaction_width, model.section_depths),
        reaction_x=float(rx),
        reaction_y=float(ry),
        reaction_moment=float(m0),
        permanent_state=evaluate_linear_static_model(linear_model, np.array([0.0, 0.0, 0.0, 0.0])),
        variable_state=evaluate_linear_static_model(linear_model, np.array([0.0, 0.0, 0.0, 1.0])),
        final_state=final_state,
    )


def estimate_required_friction(
    model: ArchLBTModel,
    upper_bound: float = 2.0,
    segment_count: int = 48,
) -> float | None:
    linear_model = build_linear_static_model(model)

    def feasible(mu: float):
        return solve_linear_interaction_lp(
            linear_model,
            fc=model.input.d_sigma,
            width=model.arch_width,
            section_depths=model.section_depths,
            segment_count=segment_count,
            friction_coefficient=mu,
        )

    high = upper_bound
    high_solution = feasible(high)
    while not high_solution.success and high < 100.0:
        high *= 2.0
        high_solution = feasible(high)
    if not high_solution.success:
        return None

    low = 0.0
    for _ in range(48):
        mid = 0.5 * (low + high)
        if feasible(mid).success:
            high = mid
        else:
            low = mid
    return high


def parabolic_interaction_diagram(
    fc: float,
    width: float,
    thickness: float,
    segment_count: int,
) -> InteractionDiagram:
    n_max = fc * width * thickness
    normal_forces = np.linspace(0.0, n_max, segment_count + 1)
    moments = normal_forces * (thickness / 2.0 - normal_forces / (2.0 * fc * width))
    return InteractionDiagram(normal_forces=normal_forces, moments=moments)


def solve_linear_interaction_lp(
    linear_model: LinearStaticModel,
    fc: float,
    width: float,
    section_depths: np.ndarray,
    segment_count: int,
    friction_coefficient: float = 0.0,
):
    rows = []
    rhs = []
    for section_depth, normal_0, normal_c, moment_0, moment_c, shear_0, shear_c in zip(
        section_depths,
        linear_model.normal_constant,
        linear_model.normal_coefficients,
        linear_model.moment_constant,
        linear_model.moment_coefficients,
        linear_model.shear_constant,
        linear_model.shear_coefficients,
    ):
        diagram = parabolic_interaction_diagram(fc, width, float(section_depth), segment_count)
        n_min = float(diagram.normal_forces[0])
        n_max = float(diagram.normal_forces[-1])
        # N >= N_min
        rows.append(-normal_c)
        rhs.append(normal_0 - n_min)
        # N <= N_max
        rows.append(normal_c)
        rhs.append(n_max - normal_0)
        # Conservative chord approximation of abs(M) <= M_R(N).
        for n0, n1, m0, m1 in zip(
            diagram.normal_forces[:-1],
            diagram.normal_forces[1:],
            diagram.moments[:-1],
            diagram.moments[1:],
        ):
            slope = (m1 - m0) / (n1 - n0)
            intercept = m0 - slope * n0
            # M <= slope*N + intercept
            rows.append(moment_c - slope * normal_c)
            rhs.append(slope * normal_0 + intercept - moment_0)
            # -M <= slope*N + intercept
            rows.append(-moment_c - slope * normal_c)
            rhs.append(slope * normal_0 + intercept + moment_0)
        if friction_coefficient > 0.0:
            # T <= mu*N
            rows.append(shear_c - friction_coefficient * normal_c)
            rhs.append(friction_coefficient * normal_0 - shear_0)
            # -T <= mu*N
            rows.append(-shear_c - friction_coefficient * normal_c)
            rhs.append(friction_coefficient * normal_0 + shear_0)

    return linprog(
        np.array([0.0, 0.0, 0.0, -1.0]),
        A_ub=np.array(rows, dtype=float),
        b_ub=np.array(rhs, dtype=float),
        bounds=[(None, None), (None, None), (None, None), (0.0, None)],
        method="highs",
    )


def find_interaction_governing_joint(
    state: StaticState,
    fc: float,
    width: float,
    section_depths: np.ndarray,
) -> int | None:
    if len(state.normal_forces) == 0:
        return None
    capacity = interaction_moment_capacity(state.normal_forces, fc, width, section_depths)
    margins = capacity - np.abs(state.moments)
    return int(np.argmin(margins))


def interaction_moment_capacity(
    normal_forces: np.ndarray,
    fc: float,
    width: float,
    section_depths: np.ndarray,
) -> np.ndarray:
    n_max = fc * width * section_depths
    clipped_normal = np.clip(normal_forces, 0.0, n_max)
    return clipped_normal * (section_depths / 2.0 - clipped_normal / (2.0 * fc * width))


def diagnose_equilibrium_only(model: ArchLBTModel) -> EquilibriumDiagnostic:
    """Check the equilibrium mapping without any strength inequalities.

    With no bounds on resultants, there is no feasibility problem to solve:
    reactions are free variables and every value defines an equilibrium field in
    the current linear mapping. This diagnostic verifies that the mapping can be
    built and evaluated with finite section resultants.
    """

    linear_model = build_linear_static_model(model)
    sample_variables = np.zeros(4, dtype=float)
    sample_state = evaluate_linear_static_model(linear_model, sample_variables)
    finite_values = bool(
        np.all(np.isfinite(sample_state.shear_forces))
        and np.all(np.isfinite(sample_state.normal_forces))
        and np.all(np.isfinite(sample_state.moments))
    )
    expected_shape = (model.joint_count,)
    shape_ok = (
        sample_state.shear_forces.shape == expected_shape
        and sample_state.normal_forces.shape == expected_shape
        and sample_state.moments.shape == expected_shape
    )
    success = finite_values and shape_ok
    message = "equilibrium mapping is evaluable" if success else "equilibrium mapping has invalid values or shapes"
    return EquilibriumDiagnostic(
        success=success,
        message=message,
        variable_count=4,
        joint_count=model.joint_count,
        finite_values=finite_values,
        sample_state=sample_state,
    )


def format_equilibrium_diagnostic(model: ArchLBTModel) -> str:
    diagnostic = diagnose_equilibrium_only(model)
    lines = [
        "ArchLBT equilibrium-only diagnostic",
        f"input = {model.input.path}",
        "",
        "No strength limits are applied in this check.",
        "Free variables = Rx, Ry, M0, lambda",
        f"status = {'OK' if diagnostic.success else 'FAILED'}",
        f"message = {diagnostic.message}",
        f"variables = {diagnostic.variable_count}",
        f"joints = {diagnostic.joint_count}",
        f"finite values = {diagnostic.finite_values}",
        "",
        "Sample state for Rx=Ry=M0=lambda=0",
        f"N min/max = {np.min(diagnostic.sample_state.normal_forces):.6f} / {np.max(diagnostic.sample_state.normal_forces):.6f}",
        f"M min/max = {np.min(diagnostic.sample_state.moments):.6f} / {np.max(diagnostic.sample_state.moments):.6f}",
        f"T min/max = {np.min(diagnostic.sample_state.shear_forces):.6f} / {np.max(diagnostic.sample_state.shear_forces):.6f}",
    ]
    return "\n".join(lines) + "\n"


def diagnose_moment_only(model: ArchLBTModel) -> ConstraintDiagnostic:
    linear_model = build_linear_static_model(model)
    solution = solve_linear_strength_lp(linear_model, model.input.thickness, include_normal=False, include_moment=True)
    return constraint_diagnostic_from_solution(
        "moment-only diagnostic",
        linear_model,
        model.input.thickness,
        solution,
    )


def constraint_diagnostic_from_solution(
    name: str,
    linear_model: LinearStaticModel,
    thickness: float,
    solution,
) -> ConstraintDiagnostic:
    if solution.success:
        variables = solution.x
        state = evaluate_linear_static_model(linear_model, variables)
        return ConstraintDiagnostic(
            name=name,
            success=True,
            status=int(solution.status),
            message=str(solution.message),
            load_factor=float(variables[3]),
            reaction_x=float(variables[0]),
            reaction_y=float(variables[1]),
            reaction_moment=float(variables[2]),
            governing_joint=find_governing_joint(state, thickness),
            final_state=state,
        )
    variables = np.zeros(4, dtype=float)
    state = evaluate_linear_static_model(linear_model, variables)
    load_factor = math.inf if int(solution.status) == 3 else 0.0
    return ConstraintDiagnostic(
        name=name,
        success=False,
        status=int(solution.status),
        message=str(solution.message),
        load_factor=load_factor,
        reaction_x=0.0,
        reaction_y=0.0,
        reaction_moment=0.0,
        governing_joint=find_governing_joint(state, thickness),
        final_state=state,
    )


def format_moment_only_diagnostic(model: ArchLBTModel) -> str:
    diagnostic = diagnose_moment_only(model)
    status_text = "OK" if diagnostic.success else "UNBOUNDED" if diagnostic.status == 3 else "FAILED"
    factor_text = "unbounded" if math.isinf(diagnostic.load_factor) else f"{diagnostic.load_factor:.6f}"
    lines = [
        "ArchLBT moment-only diagnostic",
        f"input = {model.input.path}",
        "",
        "Applied limits: abs(M) <= N*D/2",
        "Skipped limits: N >= 0",
        f"status = {status_text}",
        f"message = {diagnostic.message}",
        f"lambda_max = {factor_text}",
        f"governing joint = {'-' if diagnostic.governing_joint is None else diagnostic.governing_joint}",
        f"Rx = {diagnostic.reaction_x:.6f}",
        f"Ry = {diagnostic.reaction_y:.6f}",
        f"M0 = {diagnostic.reaction_moment:.6f}",
        "",
        f"N min/max = {np.min(diagnostic.final_state.normal_forces):.6f} / {np.max(diagnostic.final_state.normal_forces):.6f}",
        f"M min/max = {np.min(diagnostic.final_state.moments):.6f} / {np.max(diagnostic.final_state.moments):.6f}",
        f"T min/max = {np.min(diagnostic.final_state.shear_forces):.6f} / {np.max(diagnostic.final_state.shear_forces):.6f}",
    ]
    return "\n".join(lines) + "\n"


def assemble_static_state(loads: np.ndarray) -> StaticState:
    cumulative = np.flip(np.cumsum(np.flip(loads, axis=0), axis=0), axis=0)
    return StaticState(
        shear_forces=cumulative[:, 0].copy(),
        normal_forces=cumulative[:, 1].copy(),
        moments=cumulative[:, 2].copy(),
    )


def combine_states(permanent: StaticState, variable: StaticState, load_factor: float) -> StaticState:
    return StaticState(
        shear_forces=permanent.shear_forces + load_factor * variable.shear_forces,
        normal_forces=permanent.normal_forces + load_factor * variable.normal_forces,
        moments=permanent.moments + load_factor * variable.moments,
    )


def build_linear_static_model(model: ArchLBTModel) -> LinearStaticModel:
    joints = 0.5 * (model.intrados + model.extrados)
    radial_axes = unit_vectors(model.extrados - model.intrados)
    axial_axes = np.column_stack([radial_axes[:, 1], -radial_axes[:, 0]])
    permanent_loads = permanent_global_loads(model)
    variable_loads = variable_global_loads(model)

    normal_constant = np.zeros(model.joint_count, dtype=float)
    normal_coefficients = np.zeros((model.joint_count, 4), dtype=float)
    moment_constant = np.zeros(model.joint_count, dtype=float)
    moment_coefficients = np.zeros((model.joint_count, 4), dtype=float)
    shear_constant = np.zeros(model.joint_count, dtype=float)
    shear_coefficients = np.zeros((model.joint_count, 4), dtype=float)

    reaction_point = joints[0]
    for joint in range(model.joint_count):
        cut = joints[joint]
        axial = axial_axes[joint]
        radial = radial_axes[joint]
        p_force, p_moment = accumulated_load(permanent_loads, cut, joint)
        q_force, q_moment = accumulated_load(variable_loads, cut, joint)

        rx_force = np.array([1.0, 0.0])
        ry_force = np.array([0.0, 1.0])
        rx_moment = moment_about(reaction_point, rx_force, cut)
        ry_moment = moment_about(reaction_point, ry_force, cut)

        normal_constant[joint] = np.dot(p_force, axial)
        normal_coefficients[joint] = (
            np.dot(rx_force, axial),
            np.dot(ry_force, axial),
            0.0,
            np.dot(q_force, axial),
        )
        shear_constant[joint] = np.dot(-p_force, radial)
        shear_coefficients[joint] = (
            np.dot(-rx_force, radial),
            np.dot(-ry_force, radial),
            0.0,
            np.dot(-q_force, radial),
        )
        moment_constant[joint] = -p_moment
        moment_coefficients[joint] = (-rx_moment, -ry_moment, -1.0, -q_moment)

    return LinearStaticModel(
        normal_constant=normal_constant,
        normal_coefficients=normal_coefficients,
        moment_constant=moment_constant,
        moment_coefficients=moment_coefficients,
        shear_constant=shear_constant,
        shear_coefficients=shear_coefficients,
    )


def permanent_global_loads(model: ArchLBTModel) -> GlobalLoads:
    masonry_points = model.prepared.masonry_weights[:, 0:2]
    masonry_forces = np.column_stack([
        np.zeros(len(model.prepared.masonry_weights)),
        -model.arch_width * model.prepared.masonry_weights[:, 2],
    ])

    fill_points = model.prepared.fill_weights[:, 2:4]
    fill_vertical = np.column_stack([
        np.zeros(len(model.prepared.fill_weights)),
        -model.arch_width * model.prepared.fill_weights[:, 0],
    ])
    block_indices = np.arange(model.block_count)
    return GlobalLoads(
        forces=np.vstack([masonry_forces, fill_vertical]),
        points=np.vstack([masonry_points, fill_points]),
        block_indices=np.concatenate([block_indices, block_indices]),
    )


def variable_global_loads(model: ArchLBTModel) -> GlobalLoads:
    return GlobalLoads(
        forces=np.column_stack([
            np.zeros(len(model.prepared.external_loads)),
            -model.prepared.external_loads[:, 2],
        ]),
        points=model.prepared.external_loads[:, 0:2],
        block_indices=np.arange(len(model.prepared.external_loads)),
    )


def check_global_equilibrium(
    model: ArchLBTModel,
    result: LowerBoundResult,
    origin: tuple[float, float] = (0.0, 0.0),
) -> EquilibriumCheck:
    origin_vector = np.array(origin, dtype=float)
    joints = 0.5 * (model.intrados + model.extrados)
    left_point = joints[0]
    right_point = joints[-1]

    permanent = permanent_global_loads(model)
    variable = variable_global_loads(model)
    load_forces = permanent.forces + 0.0
    load_points = permanent.points
    if len(variable.forces) > 0:
        load_forces = np.vstack([load_forces, result.load_factor * variable.forces])
        load_points = np.vstack([load_points, variable.points])

    total_load_force = np.sum(load_forces, axis=0)
    total_load_moment = sum(moment_about(point, force, origin_vector) for point, force in zip(load_points, load_forces))

    left_force = np.array([result.reaction_x, result.reaction_y], dtype=float)
    right_force = -(total_load_force + left_force)
    left_moment = result.reaction_moment
    right_moment = -(
        total_load_moment
        + moment_about(left_point, left_force, origin_vector)
        + left_moment
        + moment_about(right_point, right_force, origin_vector)
    )

    residual_force = total_load_force + left_force + right_force
    residual_moment = (
        total_load_moment
        + moment_about(left_point, left_force, origin_vector)
        + left_moment
        + moment_about(right_point, right_force, origin_vector)
        + right_moment
    )
    return EquilibriumCheck(
        origin_x=float(origin_vector[0]),
        origin_y=float(origin_vector[1]),
        load_force_x=float(total_load_force[0]),
        load_force_y=float(total_load_force[1]),
        load_moment=float(total_load_moment),
        left_reaction_x=float(left_force[0]),
        left_reaction_y=float(left_force[1]),
        left_reaction_moment=float(left_moment),
        right_reaction_x=float(right_force[0]),
        right_reaction_y=float(right_force[1]),
        right_reaction_moment=float(right_moment),
        residual_force_x=float(residual_force[0]),
        residual_force_y=float(residual_force[1]),
        residual_moment=float(residual_moment),
    )


def accumulated_load(loads: GlobalLoads, cut: np.ndarray, joint: int) -> tuple[np.ndarray, float]:
    if joint <= 0:
        return np.zeros(2, dtype=float), 0.0
    mask = loads.block_indices < joint
    selected_forces = loads.forces[mask]
    selected_points = loads.points[mask]
    force = np.sum(selected_forces, axis=0)
    moment = sum(moment_about(point, load, cut) for point, load in zip(selected_points, selected_forces))
    return force, float(moment)


def moment_about(point: np.ndarray, force: np.ndarray, origin: np.ndarray) -> float:
    radius = point - origin
    return float(radius[0] * force[1] - radius[1] * force[0])


def unit_vectors(vectors: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(vectors, axis=1)
    return np.divide(vectors, lengths[:, None], out=np.zeros_like(vectors), where=lengths[:, None] > 0.0)


def solve_linear_infinite_strength_lp(linear_model: LinearStaticModel, thickness: float):
    return solve_linear_strength_lp(linear_model, thickness, include_normal=True, include_moment=True)


def solve_linear_strength_lp(
    linear_model: LinearStaticModel,
    thickness: float,
    include_normal: bool,
    include_moment: bool,
):
    half_depth = thickness / 2.0
    rows = []
    rhs = []
    for normal_0, normal_c, moment_0, moment_c in zip(
        linear_model.normal_constant,
        linear_model.normal_coefficients,
        linear_model.moment_constant,
        linear_model.moment_coefficients,
    ):
        # N >= 0 -> -N <= 0
        if include_normal:
            rows.append(-normal_c)
            rhs.append(normal_0)
        if include_moment:
            # M <= N*D/2 -> M - N*D/2 <= 0
            rows.append(moment_c - half_depth * normal_c)
            rhs.append(half_depth * normal_0 - moment_0)
            # -M <= N*D/2 -> -M - N*D/2 <= 0
            rows.append(-moment_c - half_depth * normal_c)
            rhs.append(half_depth * normal_0 + moment_0)

    objective = np.array([0.0, 0.0, 0.0, -1.0])
    if not rows:
        raise ValueError("at least one constraint family must be enabled")
    result = linprog(
        objective,
        A_ub=np.array(rows, dtype=float),
        b_ub=np.array(rhs, dtype=float),
        bounds=[(None, None), (None, None), (None, None), (0.0, None)],
        method="highs",
    )
    return result


def evaluate_linear_static_model(linear_model: LinearStaticModel, variables: np.ndarray) -> StaticState:
    return StaticState(
        shear_forces=linear_model.shear_constant + linear_model.shear_coefficients @ variables,
        normal_forces=linear_model.normal_constant + linear_model.normal_coefficients @ variables,
        moments=linear_model.moment_constant + linear_model.moment_coefficients @ variables,
    )


def find_governing_joint(state: StaticState, thickness: float) -> int | None:
    margins = state.normal_forces * thickness / 2.0 - np.abs(state.moments)
    if len(margins) == 0:
        return None
    return int(np.argmin(margins))


def maximize_infinite_strength_factor(
    permanent: StaticState,
    variable: StaticState,
    thickness: float,
) -> tuple[float, int | None]:
    half_depth = thickness / 2.0
    upper_bound = math.inf
    governing_joint: int | None = None

    for joint, (n0, n1, m0, m1) in enumerate(
        zip(
            permanent.normal_forces,
            variable.normal_forces,
            permanent.moments,
            variable.moments,
        )
    ):
        if n0 < 0.0:
            return 0.0, joint
        if abs(m0) > half_depth * n0:
            return 0.0, joint

        candidates = [
            (-n1, n0),
            (m1 - half_depth * n1, half_depth * n0 - m0),
            (-m1 - half_depth * n1, half_depth * n0 + m0),
        ]
        for coefficient, rhs in candidates:
            if coefficient <= 0.0:
                continue
            limit = rhs / coefficient
            if limit < upper_bound:
                upper_bound = max(0.0, limit)
                governing_joint = joint

    if math.isinf(upper_bound):
        return math.inf, governing_joint
    return upper_bound, governing_joint


def format_model_report(model: ArchLBTModel) -> str:
    data = model.input
    loads = model.load_summary
    result = solve_parabolic_interaction_lower_bound(model)
    equilibrium = check_global_equilibrium(model, result)
    section_depth_min = float(np.min(model.section_depths))
    section_depth_max = float(np.max(model.section_depths))
    no_shear_result = None
    required_mu = None
    if not result.success and data.sliding_coefficient > 0.0:
        no_shear_result = solve_parabolic_interaction_lower_bound(model, friction_coefficient=0.0)
        required_mu = estimate_required_friction(model)
    factor_text = "unbounded" if math.isinf(result.load_factor) else f"{result.load_factor:.6f}"
    governing_text = "-" if result.governing_joint is None else str(result.governing_joint)
    status_text = "optimal" if result.success else f"failed ({result.message})"
    if result.status == 3:
        status_text = f"unbounded ({result.message})"
    lines = [
        "ArchLBT prepared model",
        f"input = {data.path}",
        "",
        "Geometry",
        f"span = {data.span:.6g}",
        f"rise = {data.rise:.6g}",
        f"thickness D = {data.thickness:.6g}",
        f"section depth min/max = {section_depth_min:.6g} / {section_depth_max:.6g}",
        f"arch width b = {model.arch_width:.6g}",
        f"geom_CODE = {data.geom_code}",
        f"extrados mode = {model.extrados_mode}",
        f"blocks = {model.block_count}",
        f"joints = {model.joint_count}",
        "",
        "Loads",
        f"arch self-weight vertical = {loads.permanent_vertical:.6f}",
        f"backfill vertical = {loads.fill_vertical:.6f}",
        f"variable vertical = {loads.variable_vertical:.6f}",
        f"total vertical = {loads.total_vertical:.6f}",
        "",
        "Lower-bound skeleton",
        "state = permanent + lambda * variable",
        "solution = statically admissible reactions Rx, Ry, M0",
        "constraints = 0 <= N <= fc*b*D_i and abs(M) <= N*(D_i/2 - N/(2*fc*b))",
        "shear constraint = abs(T) <= mu*N" if data.sliding_coefficient > 0.0 else "shear constraint = inactive",
        f"fc = {data.d_sigma:.6g}",
        f"b = {model.arch_width:.6g}",
        f"Nmax min/max = {data.d_sigma * model.arch_width * section_depth_min:.6g} / {data.d_sigma * model.arch_width * section_depth_max:.6g}",
        f"mu = {data.sliding_coefficient:.6g}",
        f"status = {status_text}",
        f"lambda_max = {factor_text}",
        f"governing joint = {governing_text}",
        *format_governing_joint_sets(model, result),
        f"Rx = {result.reaction_x:.6f}",
        f"Ry = {result.reaction_y:.6f}",
        f"M0 = {result.reaction_moment:.6f}",
        "",
        *format_failure_diagnostics(no_shear_result, required_mu),
        "Prepared arrays",
        f"intrados/extrados = {model.prepared.intrados_extrados.shape[0]} x {model.prepared.intrados_extrados.shape[1]}",
        f"local coordinates = {model.prepared.local_coordinates.shape[0]} x {model.prepared.local_coordinates.shape[1]}",
        f"masonry loads = {model.prepared.transformed_masonry.shape[0]} x {model.prepared.transformed_masonry.shape[1]}",
        f"backfill loads = {model.prepared.transformed_fill.shape[0]} x {model.prepared.transformed_fill.shape[1]}",
        f"variable loads = {model.prepared.transformed_external.shape[0]} x {model.prepared.transformed_external.shape[1]}",
        "",
        *format_equilibrium_check(result, equilibrium),
    ]
    return "\n".join(lines) + "\n"


def format_failure_diagnostics(no_shear_result: LowerBoundResult | None, required_mu: float | None) -> list[str]:
    if no_shear_result is None:
        return []
    lines = [
        "Failure diagnostic",
        f"without shear constraint status = {'optimal' if no_shear_result.success else no_shear_result.message}",
    ]
    if no_shear_result.success:
        lines.extend(
            [
                f"without shear lambda_max = {no_shear_result.load_factor:.6f}",
                f"without shear Rx = {no_shear_result.reaction_x:.6f}",
                f"without shear Ry = {no_shear_result.reaction_y:.6f}",
                f"without shear M0 = {no_shear_result.reaction_moment:.6f}",
            ]
        )
    if required_mu is None:
        lines.append("estimated required mu = not found")
    else:
        lines.append(f"estimated required mu >= {required_mu:.6f}")
    lines.append("")
    return lines


def format_governing_joint_sets(model: ArchLBTModel, result: LowerBoundResult) -> list[str]:
    if not result.success:
        return []
    sets = governing_joint_sets(model, result)
    return [
        f"governing M-N joints = {_format_index_set(sets['interaction'])}",
        f"governing shear joints = {_format_index_set(sets['shear'])}",
        f"governing compression joints = {_format_index_set(sets['compression'])}",
        f"governing tension joints = {_format_index_set(sets['tension'])}",
    ]


def governing_joint_sets(model: ArchLBTModel, result: LowerBoundResult) -> dict[str, set[int]]:
    state = result.final_state
    capacity = interaction_moment_capacity(state.normal_forces, model.input.d_sigma, model.arch_width, model.section_depths)
    interaction_margin = capacity - np.abs(state.moments)
    if model.input.sliding_coefficient > 0.0:
        shear_margin = model.input.sliding_coefficient * state.normal_forces - np.abs(state.shear_forces)
    else:
        shear_margin = np.full_like(state.normal_forces, np.inf)
    compression_margin = model.input.d_sigma * model.arch_width * model.section_depths - state.normal_forces
    tension_margin = state.normal_forces
    return {
        "interaction": near_minimum_indices(interaction_margin),
        "shear": near_minimum_indices(shear_margin),
        "compression": near_minimum_indices(compression_margin),
        "tension": near_minimum_indices(tension_margin),
    }


def near_minimum_indices(values: np.ndarray, tolerance: float = 1e-5) -> set[int]:
    finite = values[np.isfinite(values)]
    if len(finite) == 0:
        return set()
    minimum = float(np.min(finite))
    scale = max(1.0, abs(minimum), float(np.max(np.abs(finite))))
    return {int(index) for index, value in enumerate(values) if np.isfinite(value) and value <= minimum + tolerance * scale}


def _format_index_set(indices: set[int]) -> str:
    if not indices:
        return "-"
    return ", ".join(str(index) for index in sorted(indices))


def format_equilibrium_check(result: LowerBoundResult, equilibrium: EquilibriumCheck) -> list[str]:
    if not result.success:
        return [
            "Global equilibrium check",
            "not available for failed solution; reactions above are not a valid admissible state",
            "",
        ]
    return [
        "Global equilibrium check",
        f"moment origin = [{equilibrium.origin_x:.6g}, {equilibrium.origin_y:.6g}]",
        f"loads sum Fx = {equilibrium.load_force_x:.9e}",
        f"loads sum Fy = {equilibrium.load_force_y:.9e}",
        f"loads sum M = {equilibrium.load_moment:.9e}",
        f"left reaction = [{equilibrium.left_reaction_x:.9e}, {equilibrium.left_reaction_y:.9e}], M = {equilibrium.left_reaction_moment:.9e}",
        f"right reaction = [{equilibrium.right_reaction_x:.9e}, {equilibrium.right_reaction_y:.9e}], M = {equilibrium.right_reaction_moment:.9e}",
        f"residual sum Fx = {equilibrium.residual_force_x:.9e}",
        f"residual sum Fy = {equilibrium.residual_force_y:.9e}",
        f"residual sum M = {equilibrium.residual_moment:.9e}",
        "",
    ]
