from __future__ import annotations

from pathlib import Path

from .core import Diagram


def plot_diagram(diagram: Diagram, output_path: str | Path) -> None:
    """Save the interaction diagram as an image.

    The file type is inferred by Matplotlib from the suffix, so PNG, SVG and
    PDF work out of the box.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path = Path(output_path)
    moments = [point.moment for point in diagram.points]
    axial_forces = [point.axial_force for point in diagram.points]

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=140)
    ax.plot(moments, axial_forces, color="#1f5a7a", linewidth=2.2)
    ax.scatter(moments, axial_forces, s=12, color="#d07a2d", zorder=3)
    ax.set_title(f"Interakcni diagram - METHOD={diagram.method}")
    ax.set_xlabel("Moment M")
    ax.set_ylabel("Normalova sila N")
    ax.grid(True, color="#d7dde2", linewidth=0.7)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
