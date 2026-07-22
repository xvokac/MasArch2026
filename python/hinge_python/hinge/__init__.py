"""Python port of the original HINGE.exe interaction-diagram calculator."""

from .core import Diagram, Point, compute_diagram, parse_input, render_output
from .plotting import plot_diagram

__all__ = [
    "Diagram",
    "Point",
    "compute_diagram",
    "parse_input",
    "plot_diagram",
    "render_output",
]
