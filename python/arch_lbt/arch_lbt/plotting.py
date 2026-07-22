from __future__ import annotations

import numpy as np

from .core import ArchLBTModel, LowerBoundResult, check_global_equilibrium, governing_joint_sets, parabolic_interaction_diagram


def plot_arch_view(ax, input_name: str, model: ArchLBTModel, result: LowerBoundResult) -> None:
    intrados = model.intrados
    extrados = model.extrados
    ax.clear()
    ax.plot(intrados[:, 0], intrados[:, 1], color="#1f77b4", linewidth=2.0, label="intrados")
    ax.plot(extrados[:, 0], extrados[:, 1], color="#1f77b4", linewidth=2.0, label="extrados")
    _plot_fill_surface(ax, model)
    _plot_surface_loads(ax, model)
    _plot_spread_loads(ax, model)
    for index in range(len(intrados)):
        ax.plot(
            [intrados[index, 0], extrados[index, 0]],
            [intrados[index, 1], extrados[index, 1]],
            color="#b8c2cc",
            linewidth=0.7,
        )
    if result.success:
        centers = 0.5 * (intrados + extrados)
        radial = _unit_vectors(extrados - intrados)
        eccentricity = np.divide(
            result.final_state.moments,
            result.final_state.normal_forces,
            out=np.zeros_like(result.final_state.moments),
            where=np.abs(result.final_state.normal_forces) > 1e-12,
        )
        pressure_line = centers + eccentricity[:, None] * radial
        ax.plot(pressure_line[:, 0], pressure_line[:, 1], color="#d62728", linewidth=1.8, marker="o", markersize=3, label="tlakova cara")
        _mark_governing_sets(ax, pressure_line, model, result)
    else:
        _write_infeasible_note(ax, result)
    ax.set_title(f"{input_name} - lambda = {result.load_factor:.6f}", pad=48)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#e2e8f0")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0, fontsize=8)
    _write_reaction_summary(ax, model, result)
    _reserve_arch_header_space(ax, model)


def plot_interaction_view(ax, input_name: str, model: ArchLBTModel, result: LowerBoundResult) -> None:
    depths = model.section_depths
    min_depth = float(np.min(depths))
    max_depth = float(np.max(depths))
    diagram = parabolic_interaction_diagram(model.input.d_sigma, model.arch_width, min_depth, 180)
    moments = np.abs(result.final_state.moments)
    normal_forces = result.final_state.normal_forces

    ax.clear()
    if not result.success:
        ax.text(0.5, 0.5, "Uloha je infeasible - body nejsou platny vysledek.", transform=ax.transAxes, ha="center", va="center")
        ax.set_title(f"{input_name} - M-N")
        ax.set_xlabel("Moment |M|")
        ax.set_ylabel("Normalova sila N")
        ax.grid(True, color="#d7dde2", linewidth=0.7)
        return
    ax.plot(diagram.moments, diagram.normal_forces, color="#1f5a7a", linewidth=2.0, label=f"interakce Dmin={min_depth:.4g}")
    if max_depth > min_depth * 1.000001:
        max_diagram = parabolic_interaction_diagram(model.input.d_sigma, model.arch_width, max_depth, 180)
        ax.plot(max_diagram.moments, max_diagram.normal_forces, color="#1f5a7a", linewidth=1.4, linestyle="--", label=f"interakce Dmax={max_depth:.4g}")
    ax.scatter(moments, normal_forces, color="#c43c2f", s=24, zorder=3, label="rezy klenby")
    governing_sets = _governing_sets(model, result)
    interaction = sorted(governing_sets["interaction"])
    if interaction:
        ax.scatter(moments[interaction], normal_forces[interaction], color="#111111", s=72, zorder=4, label="rozhodujici M-N")
    for index, (moment, normal_force) in enumerate(zip(moments, normal_forces)):
        ax.annotate(str(index), (moment, normal_force), xytext=(4, 3), textcoords="offset points", fontsize=7)
    ax.set_title(f"{input_name} - M-N")
    ax.set_xlabel("Moment |M|")
    ax.set_ylabel("Normalova sila N")
    ax.set_xlim(left=0.0)
    ax.set_ylim(bottom=0.0)
    ax.grid(True, color="#d7dde2", linewidth=0.7)
    ax.legend(loc="best")


def plot_shear_view(ax, input_name: str, model: ArchLBTModel, result: LowerBoundResult) -> None:
    normal_forces = result.final_state.normal_forces
    shear_forces = result.final_state.shear_forces
    mu = model.input.sliding_coefficient
    n_max = max(float(np.max(normal_forces)), model.input.d_sigma * model.arch_width * float(np.max(model.section_depths)), 1.0)
    n_axis = np.linspace(0.0, n_max * 1.04, 100)
    shear_limit = mu * n_axis
    ax.clear()
    if not result.success:
        ax.text(0.5, 0.5, "Uloha je infeasible - body nejsou platny vysledek.", transform=ax.transAxes, ha="center", va="center")
        ax.set_title(f"{input_name} - N-T, mu = {mu:.6g}")
        ax.set_xlabel("Normalova sila N")
        ax.set_ylabel("Posouvajici sila T")
        ax.grid(True, color="#d7dde2", linewidth=0.7)
        return
    if mu > 0.0:
        ax.plot(n_axis, shear_limit, color="#1f5a7a", linewidth=2.0, label="T = mu N")
        ax.plot(n_axis, -shear_limit, color="#1f5a7a", linewidth=2.0, linestyle="--", label="T = -mu N")
    ax.scatter(normal_forces, shear_forces, color="#c43c2f", s=24, zorder=3, label="rezy klenby")
    governing_sets = _governing_sets(model, result)
    shear = sorted(governing_sets["shear"])
    if shear:
        ax.scatter(normal_forces[shear], shear_forces[shear], color="#f28e2b", s=72, zorder=4, label="rozhodujici smyk")
    for index, (normal_force, shear_force) in enumerate(zip(normal_forces, shear_forces)):
        ax.annotate(str(index), (normal_force, shear_force), xytext=(4, 3), textcoords="offset points", fontsize=7)
    ax.set_title(f"{input_name} - N-T, mu = {mu:.6g}")
    ax.set_xlabel("Normalova sila N")
    ax.set_ylabel("Posouvajici sila T")
    ax.set_xlim(left=0.0)
    y_extent = max(float(np.max(np.abs(shear_forces))), float(np.max(shear_limit)) if mu > 0.0 else 1.0, 1.0)
    ax.set_ylim(-1.08 * y_extent, 1.08 * y_extent)
    ax.grid(True, color="#d7dde2", linewidth=0.7)
    ax.legend(loc="best")


def _plot_fill_surface(ax, model: ArchLBTModel) -> None:
    data = model.input
    if data.fill_height <= 0.0:
        return
    extrados = model.extrados
    top_y = data.rise + data.thickness + data.fill_height
    ax.fill_between(extrados[:, 0], extrados[:, 1], top_y, where=top_y >= extrados[:, 1], color="#d8c6a3", alpha=0.28, linewidth=0.0)
    ax.plot([float(np.min(extrados[:, 0])), float(np.max(extrados[:, 0]))], [top_y, top_y], color="#8a6f3d", linewidth=1.2, linestyle="--", label="nadnasyp")


def _plot_surface_loads(ax, model: ArchLBTModel) -> None:
    data = model.input
    if not data.point_loads:
        return
    top_y = data.rise + data.thickness + data.fill_height
    y_min = float(min(np.min(model.extrados[:, 1]), top_y))
    plot_scale = max(abs(top_y - y_min), data.thickness, 1.0)
    arrow_length = 0.10 * plot_scale
    label_step = 0.055 * plot_scale
    highest_label_y = top_y + arrow_length + 2.4 * label_step
    for index, load in enumerate(data.point_loads):
        half_width = max(_surface_load_width(model, load) / 2.0, 0.015 * max(float(np.ptp(model.extrados[:, 0])), data.span, 1.0))
        ax.plot([load.x - half_width, load.x + half_width], [top_y, top_y], color="#6f3fa0", linewidth=3.0, solid_capstyle="butt", label="zatizeni" if index == 0 else None)
        ax.arrow(load.x, top_y + arrow_length, 0.0, -arrow_length, width=0.0025, head_width=0.035, head_length=0.035, color="#6f3fa0", length_includes_head=True)
        label_y = top_y + arrow_length + label_step * (1 + index % 2)
        ax.text(
            load.x,
            label_y,
            f"F={_fmt_plot_value(load.force)}, b={_fmt_plot_value(load.width)}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#4a2574",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "#6f3fa0", "alpha": 0.86, "linewidth": 0.7},
        )
    current_bottom, current_top = ax.get_ylim()
    ax.set_ylim(current_bottom, max(current_top, highest_label_y + 0.10 * plot_scale))


def _plot_spread_loads(ax, model: ArchLBTModel) -> None:
    loads = model.prepared.external_loads
    nonzero = loads[np.abs(loads[:, 2]) > 1e-10]
    if len(nonzero) == 0:
        return
    y_limits = ax.get_ylim()
    length = 0.08 * abs(y_limits[1] - y_limits[0] if y_limits[1] != y_limits[0] else 1.0)
    for index, (x, y, _force) in enumerate(nonzero):
        ax.arrow(x, y + length, 0.0, -length, width=0.003, head_width=0.025, head_length=0.025, color="#2ca02c", length_includes_head=True, label="roznesene zatizeni" if index == 0 else None)


def _surface_load_width(model: ArchLBTModel, load) -> float:
    data = model.input
    if data.q_code == 0:
        return load.width
    top_y = data.rise + data.thickness + data.fill_height
    surface_y = float(np.interp(load.x, model.extrados[:, 0], model.extrados[:, 1]))
    return load.width + 2.0 * max(0.0, top_y - surface_y) * np.tan(data.fill_spread_angle)


def _mark_governing_sets(ax, pressure_line: np.ndarray, model: ArchLBTModel, result: LowerBoundResult) -> None:
    governing_sets = _governing_sets(model, result)
    _mark_indices(ax, pressure_line, governing_sets["interaction"], "#111111", "rozhodujici M-N")
    _mark_shear_joints(ax, model, governing_sets["shear"])
    for index in sorted(governing_sets["interaction"]):
        ax.annotate(str(index), (pressure_line[index, 0], pressure_line[index, 1]), xytext=(5, 4), textcoords="offset points", fontsize=8)


def _mark_indices(ax, points: np.ndarray, indices: set[int], color: str, label: str) -> None:
    if not indices:
        return
    ordered = sorted(indices)
    ax.scatter(points[ordered, 0], points[ordered, 1], s=76, color=color, zorder=7, label=label)


def _mark_shear_joints(ax, model: ArchLBTModel, indices: set[int]) -> None:
    if not indices:
        return
    for label_index, joint in enumerate(sorted(indices)):
        ax.plot(
            [model.intrados[joint, 0], model.extrados[joint, 0]],
            [model.intrados[joint, 1], model.extrados[joint, 1]],
            color="#f28e2b",
            linewidth=3.2,
            solid_capstyle="round",
            zorder=6,
            label="rozhodujici smyk" if label_index == 0 else None,
        )
        point = 0.5 * (model.intrados[joint] + model.extrados[joint])
        ax.annotate(str(joint), (point[0], point[1]), xytext=(5, -10), textcoords="offset points", fontsize=8, color="#8a4b00")


def _governing_sets(model: ArchLBTModel, result: LowerBoundResult) -> dict[str, set[int]]:
    return governing_joint_sets(model, result)


def _write_reaction_summary(ax, model: ArchLBTModel, result: LowerBoundResult) -> None:
    if not result.success:
        text = "Reakce nejsou k dispozici: uloha je infeasible pro zadane podminky."
        ax.text(
            0.5,
            1.015,
            text,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=8,
            color="#7f1d1d",
            bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#ef4444", "alpha": 0.92, "linewidth": 0.7},
            clip_on=False,
        )
        return
    equilibrium = check_global_equilibrium(model, result)
    text = (
        "Reakce vlevo: "
        f"Rx={_fmt_plot_value(equilibrium.left_reaction_x)}, "
        f"Ry={_fmt_plot_value(equilibrium.left_reaction_y)}, "
        f"M={_fmt_plot_value(equilibrium.left_reaction_moment)}\n"
        "Reakce vpravo: "
        f"Rx={_fmt_plot_value(equilibrium.right_reaction_x)}, "
        f"Ry={_fmt_plot_value(equilibrium.right_reaction_y)}, "
        f"M={_fmt_plot_value(equilibrium.right_reaction_moment)}"
    )
    ax.text(
        0.5,
        1.015,
        text,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8,
        color="#222222",
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#94a3b8", "alpha": 0.92, "linewidth": 0.7},
        clip_on=False,
    )


def _write_infeasible_note(ax, result: LowerBoundResult) -> None:
    ax.text(
        0.5,
        0.16,
        f"Infeasible: {result.message}",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8,
        color="#7f1d1d",
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#ef4444", "alpha": 0.92, "linewidth": 0.7},
    )


def _reserve_arch_header_space(ax, model: ArchLBTModel) -> None:
    data = model.input
    top_y = data.rise + data.thickness + max(data.fill_height, 0.0)
    current_bottom, current_top = ax.get_ylim()
    y_span = max(current_top - current_bottom, data.thickness, 1.0)
    header_top = top_y + 0.34 * y_span
    ax.set_ylim(current_bottom, max(current_top, header_top))


def _unit_vectors(vectors: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(vectors, axis=1)
    return np.divide(vectors, lengths[:, None], out=np.zeros_like(vectors), where=lengths[:, None] > 0.0)


def _fmt_plot_value(value: float) -> str:
    return f"{value:.4g}"
