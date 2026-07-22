from __future__ import annotations

from pathlib import Path

from .core import AnalysisResult


def plot_arch(result: AnalysisResult, output_path: str | Path) -> None:
    """Save the arch geometry and pressure line as a Matplotlib figure."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = result.data
    if len(result.internal_forces) != len(data.x):
        raise ValueError("Cannot plot arch: internal force results are unavailable.")

    x = list(data.x)
    intrados_y = list(data.y)
    extrados_y = [data.y[i] + data.nd[i] * result.d for i in range(len(data.x))]
    pressure_y = [
        data.y[i] + data.nd[i] * result.d / 2.0 + result.internal_forces[i].e
        for i in range(len(data.x))
    ]

    path = Path(output_path)
    fig, ax = plt.subplots(figsize=(8.0, 4.8), dpi=150)
    ax.plot(x, intrados_y, color="#2f5d50", linewidth=2.0, label="Intrados")
    ax.plot(x, extrados_y, color="#8c5a2b", linewidth=2.0, label="Extrados")
    ax.plot(x, pressure_y, color="#b21f2d", linewidth=2.2, label="Tlakova cara")
    ax.scatter(x, pressure_y, color="#b21f2d", s=14, zorder=4)

    for index in result.result_pins:
        ax.axvline(data.x[index], color="#7f8790", linewidth=0.7, linestyle=":")

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_title(
        f"MArch MODE {data.mode}: D={result.d:.6g}, alpha={result.alfa:.6g}"
    )
    ax.grid(True, color="#d7dde2", linewidth=0.7)
    ax.legend(loc="best")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
