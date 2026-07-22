from __future__ import annotations

import argparse
import csv
from pathlib import Path
import traceback

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

from arch_lbt import check_global_equilibrium, estimate_required_friction, governing_joint_sets, parabolic_interaction_diagram, read_model, solve_parabolic_interaction_lower_bound
from arch_lbt.plotting import plot_arch_view, plot_interaction_view, plot_shear_view


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run ArchLBT parabolic-interaction lower-bound analysis for *lbt.in inputs."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory with input files. Default: current directory.",
    )
    parser.add_argument(
        "--pattern",
        default="*lbt.in",
        help="Input glob pattern. Default: *lbt.in.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "arch_lbt_outputs",
        help="Directory for CSV/report outputs. Default: ./arch_lbt_outputs.",
    )
    args = parser.parse_args()

    input_paths = sorted(args.input_dir.glob(args.pattern))
    if not input_paths:
        raise SystemExit(f"No input files matched {args.input_dir / args.pattern}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for input_path in input_paths:
        output_stem = input_path.stem if input_path.stem.endswith("_lbt") else f"{input_path.stem}_lbt"
        report_path = args.output_dir / f"{output_stem}.txt"
        plot_path = args.output_dir / f"{output_stem}_arch.png"
        interaction_plot_path = args.output_dir / f"{output_stem}_interaction.png"
        shear_plot_path = args.output_dir / f"{output_stem}_shear.png"
        try:
            model = read_model(input_path)
            result = solve_parabolic_interaction_lower_bound(model)
            report_path.write_text(format_case_report(input_path, model, result), encoding="utf-8")
            plot_arch_lbt(input_path.name, model, result, plot_path)
            plot_interaction_plasticity(input_path.name, model, result, interaction_plot_path)
            plot_shear_plasticity(input_path.name, model, result, shear_plot_path)
            rows.append(
                {
                    "input": input_path.name,
                    "status": "OK" if result.success else "FAILED",
                    "message": result.message,
                    "lambda_max": result.load_factor,
                    "governing_joint": "" if result.governing_joint is None else result.governing_joint,
                    "Rx": result.reaction_x,
                    "Ry": result.reaction_y,
                    "M0": result.reaction_moment,
                    "N_min": float(result.final_state.normal_forces.min()),
                    "N_max": float(result.final_state.normal_forces.max()),
                    "M_min": float(result.final_state.moments.min()),
                    "M_max": float(result.final_state.moments.max()),
                    "report": str(report_path),
                    "plot": str(plot_path),
                    "interaction_plot": str(interaction_plot_path),
                    "shear_plot": str(shear_plot_path),
                }
            )
        except Exception as exc:  # noqa: BLE001
            error_path = args.output_dir / f"{input_path.stem}_error.txt"
            error_path.write_text(traceback.format_exc(), encoding="utf-8")
            rows.append(
                {
                    "input": input_path.name,
                    "status": "ERROR",
                    "message": str(exc).splitlines()[0],
                    "lambda_max": "",
                    "governing_joint": "",
                    "Rx": "",
                    "Ry": "",
                    "M0": "",
                    "N_min": "",
                    "N_max": "",
                    "M_min": "",
                    "M_max": "",
                    "report": str(error_path),
                    "plot": "",
                    "interaction_plot": "",
                    "shear_plot": "",
                }
            )

    summary_path = args.output_dir / "arch_lbt_summary.csv"
    write_summary(summary_path, rows)
    print(f"Processed {len(input_paths)} input files.")
    print(f"Summary: {summary_path}")
    return 0


def format_case_report(input_path: Path, model, result) -> str:
    status = "optimal" if result.success else result.message
    equilibrium = check_global_equilibrium(model, result)
    section_depth_min = float(np.min(model.section_depths))
    section_depth_max = float(np.max(model.section_depths))
    no_shear_result = solve_parabolic_interaction_lower_bound(model, friction_coefficient=0.0) if not result.success and model.input.sliding_coefficient > 0.0 else None
    required_mu = estimate_required_friction(model) if no_shear_result is not None else None
    return "\n".join(
        [
            "ArchLBT parabolic interaction result",
            f"input = {input_path}",
            f"status = {status}",
            f"lambda_max = {result.load_factor:.6f}",
            f"governing_joint = {'-' if result.governing_joint is None else result.governing_joint}",
            *format_governing_joint_sets(model, result),
            f"Rx = {result.reaction_x:.6f}",
            f"Ry = {result.reaction_y:.6f}",
            f"M0 = {result.reaction_moment:.6f}",
            "",
            f"fc = {model.input.d_sigma:.6f}",
            f"b = {model.arch_width:.6f}",
            f"D = {model.input.thickness:.6f}",
            f"section depth min/max = {section_depth_min:.6f} / {section_depth_max:.6f}",
            f"N_max min/max = {model.input.d_sigma * model.arch_width * section_depth_min:.6f} / {model.input.d_sigma * model.arch_width * section_depth_max:.6f}",
            "",
            f"N min/max = {result.final_state.normal_forces.min():.6f} / {result.final_state.normal_forces.max():.6f}",
            f"M min/max = {result.final_state.moments.min():.6f} / {result.final_state.moments.max():.6f}",
            f"T min/max = {result.final_state.shear_forces.min():.6f} / {result.final_state.shear_forces.max():.6f}",
            "",
            *format_failure_diagnostics(no_shear_result, required_mu),
            *format_equilibrium_check(result, equilibrium),
        ]
    )


def format_failure_diagnostics(no_shear_result, required_mu) -> list[str]:
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
    lines.append("estimated required mu = not found" if required_mu is None else f"estimated required mu >= {required_mu:.6f}")
    lines.append("")
    return lines


def format_governing_joint_sets(model, result) -> list[str]:
    if not result.success:
        return []
    sets = governing_joint_sets(model, result)
    return [
        f"governing M-N joints = {format_index_set(sets['interaction'])}",
        f"governing shear joints = {format_index_set(sets['shear'])}",
        f"governing compression joints = {format_index_set(sets['compression'])}",
        f"governing tension joints = {format_index_set(sets['tension'])}",
    ]


def format_index_set(indices: set[int]) -> str:
    if not indices:
        return "-"
    return ", ".join(str(index) for index in sorted(indices))


def format_equilibrium_check(result, equilibrium) -> list[str]:
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


def plot_arch_lbt(input_name: str, model, result, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 5.1), dpi=150)
    plot_arch_view(ax, input_name, model, result)
    fig.subplots_adjust(right=0.78, top=0.72, bottom=0.10)
    fig.savefig(output_path)
    plt.close(fig)
    crop_vertical_whitespace(output_path)


def crop_vertical_whitespace(path: Path, threshold: float = 0.972, padding: int = 10) -> None:
    image = mpimg.imread(path)
    rgb = image[:, :, :3]
    alpha = image[:, :, 3] if image.shape[2] > 3 else np.ones(image.shape[:2], dtype=rgb.dtype)
    non_white = (np.any(rgb < threshold, axis=2)) & (alpha > 0.0)
    rows = np.flatnonzero(np.any(non_white, axis=1))
    if len(rows) == 0:
        return
    top = max(int(rows[0]) - padding, 0)
    bottom = min(int(rows[-1]) + padding + 1, image.shape[0])
    if top == 0 and bottom == image.shape[0]:
        return
    mpimg.imsave(path, image[top:bottom, :, :])


def plot_interaction_plasticity(input_name: str, model, result, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 5.2), dpi=150)
    plot_interaction_view(ax, input_name, model, result)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_shear_plasticity(input_name: str, model, result, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 5.2), dpi=150)
    plot_shear_view(ax, input_name, model, result)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def limit_margins(model, result) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    diagram = parabolic_interaction_diagram(model.input.d_sigma, model.arch_width, float(np.min(model.section_depths)), 96)
    state = result.final_state
    capacity = np.interp(
        np.clip(state.normal_forces, diagram.normal_forces[0], diagram.normal_forces[-1]),
        diagram.normal_forces,
        diagram.moments,
    )
    interaction_margin = capacity - np.abs(state.moments)
    if model.input.sliding_coefficient > 0.0:
        shear_margin = model.input.sliding_coefficient * state.normal_forces - np.abs(state.shear_forces)
    else:
        shear_margin = np.full_like(state.normal_forces, np.inf)
    compression_margin = model.input.d_sigma * model.arch_width * model.section_depths - state.normal_forces
    tension_margin = state.normal_forces
    return interaction_margin, shear_margin, compression_margin, tension_margin


def plot_fill_surface(ax, data, extrados: np.ndarray) -> None:
    if data.fill_height <= 0.0:
        return
    top_y = data.rise + data.thickness + data.fill_height
    x_min = float(np.min(extrados[:, 0]))
    x_max = float(np.max(extrados[:, 0]))
    ax.fill_between(
        extrados[:, 0],
        extrados[:, 1],
        top_y,
        where=top_y >= extrados[:, 1],
        color="#d8c6a3",
        alpha=0.28,
        linewidth=0.0,
        label="nadnasyp",
    )
    ax.plot(
        [x_min, x_max],
        [top_y, top_y],
        color="#8a6f3d",
        linewidth=1.2,
        linestyle="--",
        label="horni okraj nadnasypu",
    )


def plot_input_loads(ax, data, extrados: np.ndarray) -> None:
    if not data.point_loads:
        return
    top_y = data.rise + data.thickness + data.fill_height
    y_min = float(min(np.min(extrados[:, 1]), top_y))
    y_span = max(abs(top_y - y_min), data.thickness, 1.0)
    arrow_length = 0.10 * y_span
    width_floor = 0.015 * max(float(np.ptp(extrados[:, 0])), data.span, 1.0)
    for index, load in enumerate(data.point_loads):
        half_width = max(surface_load_width(data, load, extrados) / 2.0, width_floor)
        label = "zatizeni na povrchu" if index == 0 else None
        ax.plot(
            [load.x - half_width, load.x + half_width],
            [top_y, top_y],
            color="#6f3fa0",
            linewidth=3.0,
            solid_capstyle="butt",
            label=label,
        )
        ax.arrow(
            load.x,
            top_y + arrow_length,
            0.0,
            -arrow_length,
            width=0.0025,
            head_width=0.035,
            head_length=0.035,
            color="#6f3fa0",
            length_includes_head=True,
        )


def plot_block_loads(ax, loads: np.ndarray) -> None:
    nonzero = loads[np.abs(loads[:, 2]) > 1e-10]
    if len(nonzero) == 0:
        return
    y_span = ax.get_ylim()[1] - ax.get_ylim()[0] if ax.get_ylim()[1] != ax.get_ylim()[0] else 1.0
    length = 0.08 * abs(y_span)
    for index, (x, y, force) in enumerate(nonzero):
        ax.arrow(
            x,
            y + length,
            0.0,
            -length,
            width=0.003,
            head_width=0.025,
            head_length=0.025,
            color="#2ca02c",
            length_includes_head=True,
            label="roznesene zatizeni" if index == 0 else None,
        )


def surface_load_width(data, load, extrados: np.ndarray) -> float:
    if data.q_code == 0:
        return load.width
    top_y = data.rise + data.thickness + data.fill_height
    surface_y = interpolate_extrados_y(load.x, extrados)
    spread_width = load.width + 2.0 * max(0.0, top_y - surface_y) * np.tan(data.fill_spread_angle)
    return spread_width


def interpolate_extrados_y(x: float, extrados: np.ndarray) -> float:
    if x <= extrados[0, 0]:
        return float(extrados[0, 1])
    if x >= extrados[-1, 0]:
        return float(extrados[-1, 1])
    for start, end in zip(extrados[:-1], extrados[1:]):
        if start[0] <= x <= end[0]:
            if end[0] == start[0]:
                return float(start[1])
            ratio = (x - start[0]) / (end[0] - start[0])
            return float(start[1] + ratio * (end[1] - start[1]))
    return float(extrados[-1, 1])


def governing_indices(
    interaction_margin: np.ndarray,
    shear_margin: np.ndarray,
    compression_margin: np.ndarray,
    tension_margin: np.ndarray,
) -> dict[str, set[int]]:
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
    scale = max(1.0, abs(minimum))
    return {int(index) for index, value in enumerate(values) if np.isfinite(value) and value <= minimum + tolerance * scale}


def mark_governing(ax, points: np.ndarray, indices: set[int], color: str, label: str) -> None:
    if not indices:
        return
    ordered = sorted(indices)
    ax.scatter(points[ordered, 0], points[ordered, 1], s=68, color=color, zorder=7, label=label)


def unit_vectors(vectors: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(vectors, axis=1)
    return np.divide(vectors, lengths[:, None], out=np.zeros_like(vectors), where=lengths[:, None] > 0.0)


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "input",
        "status",
        "message",
        "lambda_max",
        "governing_joint",
        "Rx",
        "Ry",
        "M0",
        "N_min",
        "N_max",
        "M_min",
        "M_max",
        "report",
        "plot",
        "interaction_plot",
        "shear_plot",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
