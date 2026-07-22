from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import traceback

import matplotlib.pyplot as plt
import numpy as np

from melb_regression.builder import read_melb_input
from melb_regression.output import write_melb_outputs


@dataclass(frozen=True)
class InteractionDiagram:
    normal_forces: np.ndarray
    moments: np.ndarray


@dataclass(frozen=True)
class SectionResults:
    joints: np.ndarray
    normal_forces: np.ndarray
    normal_distances: np.ndarray
    moments: np.ndarray


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run MELB inputs, export txt/out files, extract final N/e values, "
            "and plot them into a HINGE interaction diagram."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory with input files. Default: current directory.",
    )
    parser.add_argument(
        "--pattern",
        default="klenba_*.in",
        help="Input glob pattern. Default: klenba_*.in.",
    )
    parser.add_argument(
        "--interaction",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "hinge_python" / "hinge_input.out",
        help="HINGE interaction diagram output. Default: ../hinge_python/hinge_input.out.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "klenba_batch_outputs",
        help="Directory for exported txt/out/png/csv files. Default: ./klenba_batch_outputs.",
    )
    args = parser.parse_args()

    input_paths = sorted(args.input_dir.glob(args.pattern))
    if not input_paths:
        raise SystemExit(f"No input files matched {args.input_dir / args.pattern}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    interaction = read_interaction_diagram(args.interaction)
    summary_rows = []

    for input_path in input_paths:
        txt_path = args.output_dir / f"{input_path.stem}.txt"
        out_path = args.output_dir / f"{input_path.stem}.out"
        png_path = args.output_dir / f"{input_path.stem}_interaction.png"
        arch_png_path = args.output_dir / f"{input_path.stem}_arch.png"

        try:
            data = read_melb_input(input_path)
            result = write_melb_outputs(input_path, txt_path, out_path)
            sections = read_final_section_results(txt_path, data.thickness)
            reduction_factor = find_reduction_factor(interaction, sections)
            plot_interaction(input_path.name, interaction, sections, reduction_factor, png_path)
            plot_arch(input_path.name, result.final, arch_png_path)
        except Exception as exc:  # noqa: BLE001
            summary_rows.append(
                {
                    "input": input_path.name,
                    "status": "ERROR",
                    "error": str(exc).splitlines()[0],
                    "joint": "",
                    "N": "",
                    "e": "",
                    "D": "",
                    "M": "",
                    "M_abs": "",
                    "reduction_factor": "",
                    "N_red": "",
                    "M_abs_red": "",
                    "txt": str(txt_path) if txt_path.exists() else "",
                    "out": str(out_path) if out_path.exists() else "",
                    "plot": "",
                    "arch_plot": "",
                }
            )
            (args.output_dir / f"{input_path.stem}_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            continue

        for joint, normal_force, normal_distance, moment in zip(
            sections.joints,
            sections.normal_forces,
            sections.normal_distances,
            sections.moments,
        ):
            summary_rows.append(
                {
                    "input": input_path.name,
                    "status": "OK",
                    "error": "",
                    "joint": int(joint),
                    "N": float(normal_force),
                    "e": float(normal_distance),
                    "D": data.thickness,
                    "M": float(moment),
                    "M_abs": abs(float(moment)),
                    "reduction_factor": reduction_factor,
                    "N_red": float(normal_force) * reduction_factor,
                    "M_abs_red": abs(float(moment)) * reduction_factor,
                    "txt": str(txt_path),
                    "out": str(out_path),
                    "plot": str(png_path),
                    "arch_plot": str(arch_png_path),
                }
            )

    write_summary(args.output_dir / "klenba_sections_summary.csv", summary_rows)
    print(f"Processed {len(input_paths)} input files.")
    print(f"Output directory: {args.output_dir}")
    return 0


def read_interaction_diagram(path: Path) -> InteractionDiagram:
    text = path.read_text(encoding="cp1250", errors="ignore")
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            rows.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue
    if not rows:
        raise ValueError(f"No N/M rows found in interaction diagram: {path}")
    values = np.array(rows, dtype=float)
    return InteractionDiagram(normal_forces=values[:, 0], moments=values[:, 1])


def read_final_section_results(txt_path: Path, thickness: float) -> SectionResults:
    text = txt_path.read_text(encoding="utf-8", errors="ignore")
    final_text = text[text.rfind(" icase = ") :]
    if not final_text:
        raise ValueError(f"No final result block found in {txt_path}")

    joints = parse_vector_after(final_text, "Vektor indexu spary mezi bloky:")
    normal_forces = parse_vector_after(final_text, "Vektor normalovych sil ve sparach")
    normal_distances = parse_vector_after(final_text, "Vektor vzdalenosti N od hornoho povrchu klenby:")
    if not (len(joints) == len(normal_forces) == len(normal_distances)):
        raise ValueError(
            f"Final result vector lengths differ in {txt_path}: "
            f"joints={len(joints)}, N={len(normal_forces)}, e={len(normal_distances)}"
        )
    moments = normal_forces * (normal_distances - thickness / 2.0)
    return SectionResults(joints, normal_forces, normal_distances, moments)


def parse_vector_after(text: str, marker: str) -> np.ndarray:
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"Vector not found: {marker}")
    numbers: list[float] = []
    for line in text[start + len(marker) :].splitlines()[1:]:
        values = parse_numeric_line(line)
        if not values:
            if numbers:
                break
            continue
        numbers.extend(values)
        if len(values) < 3:
            break
    if not numbers:
        raise ValueError(f"Vector is empty: {marker}")
    return np.array(numbers, dtype=float)


def parse_numeric_line(line: str) -> list[float]:
    values = []
    for part in line.split():
        try:
            values.append(float(part))
        except ValueError:
            return []
    return values


def find_reduction_factor(interaction: InteractionDiagram, sections: SectionResults) -> float:
    section_moments = np.abs(sections.moments)
    if points_inside_interaction(interaction, section_moments, sections.normal_forces, 1.0):
        return 1.0

    low = 0.0
    high = 1.0
    for _ in range(80):
        mid = (low + high) / 2.0
        if points_inside_interaction(interaction, section_moments, sections.normal_forces, mid):
            low = mid
        else:
            high = mid
    return low


def points_inside_interaction(
    interaction: InteractionDiagram,
    moments: np.ndarray,
    normal_forces: np.ndarray,
    factor: float,
) -> bool:
    scaled_moments = factor * moments
    scaled_normal_forces = factor * normal_forces
    if np.any(scaled_normal_forces < interaction.normal_forces[0] - 1e-9):
        return False
    if np.any(scaled_normal_forces > interaction.normal_forces[-1] + 1e-9):
        return False
    capacities = np.interp(scaled_normal_forces, interaction.normal_forces, interaction.moments)
    return bool(np.all(scaled_moments <= capacities + 1e-9))


def plot_interaction(
    input_name: str,
    interaction: InteractionDiagram,
    sections: SectionResults,
    reduction_factor: float,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 5.2), dpi=150)
    section_moments = np.abs(sections.moments)
    reduced_moments = section_moments * reduction_factor
    reduced_normal_forces = sections.normal_forces * reduction_factor
    ax.plot(interaction.moments, interaction.normal_forces, color="#1f5a7a", linewidth=2.0, label="interakcni diagram")
    ax.scatter(section_moments, sections.normal_forces, color="#c43c2f", s=24, zorder=3, label="rezy klenby")
    if reduction_factor < 0.999999:
        ax.scatter(
            reduced_moments,
            reduced_normal_forces,
            color="#2f8f46",
            s=24,
            zorder=4,
            label="redukovane sily",
        )
    for joint, moment, normal_force in zip(sections.joints, section_moments, sections.normal_forces):
        ax.annotate(
            str(int(joint)),
            (moment, normal_force),
            xytext=(4, 3),
            textcoords="offset points",
            fontsize=7,
            color="#333333",
        )
    if reduction_factor < 0.999999:
        ax.text(
            0.02,
            0.98,
            f"redukcni nasobek = {reduction_factor:.4f}",
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=10,
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#b7c0c7", "alpha": 0.9},
        )
    else:
        ax.text(
            0.02,
            0.98,
            "redukcni nasobek = 1.0000",
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=10,
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#b7c0c7", "alpha": 0.9},
        )
    ax.set_title(input_name)
    ax.set_xlabel("Moment M")
    ax.set_ylabel("Normalova sila N")
    ax.grid(True, color="#d7dde2", linewidth=0.7)
    ax.set_xlim(left=0.0)
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_arch(input_name: str, step, output_path: Path) -> None:
    data = step.prepared.input
    geom = step.prepared.intrados_extrados
    intrados = geom[:, 0:2]
    extrados = geom[:, 2:4]
    pressure = pressure_line(step)
    active = np.flatnonzero(step.mechanism[: 2 * len(intrados)] > 1e-5)

    fig, ax = plt.subplots(figsize=(8.0, 5.2), dpi=150)
    ax.plot(intrados[:, 0], intrados[:, 1], color="#1f77b4", linewidth=2.0, label="intrados")
    ax.plot(extrados[:, 0], extrados[:, 1], color="#1f77b4", linewidth=2.0, label="extrados")
    plot_fill_surface(ax, data, extrados)
    plot_input_loads(ax, data, extrados)
    for index in range(len(intrados)):
        ax.plot(
            [intrados[index, 0], extrados[index, 0]],
            [intrados[index, 1], extrados[index, 1]],
            color="#b8c2cc",
            linewidth=0.7,
        )
    plot_sliding_joints(ax, step, intrados, extrados)
    ax.plot(pressure[:, 0], pressure[:, 1], color="#d62728", linewidth=1.8, marker="o", markersize=3, label="N")
    for variable in active:
        joint = variable // 2
        point = intrados[joint] if variable % 2 == 0 else extrados[joint]
        ax.scatter([point[0]], [point[1]], s=55, color="#111111", zorder=5)
    plot_loads(ax, step.prepared.external_loads)
    ax.set_title(f"{input_name} - lambda = {step.load_factor:.6f}")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#e2e8f0")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0, fontsize=8)
    fig.subplots_adjust(right=0.78)
    fig.savefig(output_path)
    plt.close(fig)


def pressure_line(step) -> np.ndarray:
    geom = step.prepared.intrados_extrados
    intrados = geom[:, 0:2]
    extrados = geom[:, 2:4]
    thickness = np.linalg.norm(intrados - extrados, axis=1)
    ratio = np.divide(step.normal_distances, thickness, out=np.zeros_like(step.normal_distances), where=thickness > 0.0)
    ratio = np.clip(ratio, 0.0, 1.0)
    return extrados + ratio[:, None] * (intrados - extrados)


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
    ax.plot([x_min, x_max], [top_y, top_y], color="#8a6f3d", linewidth=1.2, linestyle="--", label="horni okraj nadnasypu")


def plot_input_loads(ax, data, extrados: np.ndarray) -> None:
    if not data.point_loads:
        return
    top_y = data.rise + data.thickness + data.fill_height
    y_min = float(min(np.min(extrados[:, 1]), top_y))
    y_span = max(abs(top_y - y_min), data.thickness, 1.0)
    arrow_length = 0.10 * y_span
    width_floor = 0.015 * max(float(np.ptp(extrados[:, 0])), data.span, 1.0)
    for index, load in enumerate(data.point_loads):
        half_width = max(load.width / 2.0, width_floor)
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


def plot_sliding_joints(ax, step, intrados: np.ndarray, extrados: np.ndarray) -> None:
    joint_count = len(intrados)
    offset = 2 * joint_count
    if step.prepared.input.sliding_coefficient <= 0.0 or len(step.mechanism) <= offset:
        return
    sliding = step.mechanism[offset : offset + 2 * joint_count]
    active_joints = sorted({index // 2 for index, value in enumerate(sliding) if abs(value) > 1e-5})
    for position, joint in enumerate(active_joints):
        if joint >= joint_count:
            continue
        ax.plot(
            [intrados[joint, 0], extrados[joint, 0]],
            [intrados[joint, 1], extrados[joint, 1]],
            color="#f28e2b",
            linewidth=4.0,
            solid_capstyle="round",
            label="smykova porucha" if position == 0 else None,
            zorder=6,
        )


def plot_loads(ax, loads: np.ndarray) -> None:
    nonzero = loads[np.abs(loads[:, 2]) > 1e-10]
    if len(nonzero) == 0:
        return
    y_span = ax.get_ylim()[1] - ax.get_ylim()[0] if ax.get_ylim()[1] != ax.get_ylim()[0] else 1.0
    length = 0.08 * abs(y_span)
    for x, y, force in nonzero:
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
        )


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "input",
        "status",
        "error",
        "joint",
        "N",
        "e",
        "D",
        "M",
        "M_abs",
        "reduction_factor",
        "N_red",
        "M_abs_red",
        "txt",
        "out",
        "plot",
        "arch_plot",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
