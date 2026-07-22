from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .core import compute_diagram, parse_input, render_output
from .gui import main as gui_main
from .plotting import plot_diagram


def main() -> int:
    if len(sys.argv) == 1:
        return gui_main()

    parser = argparse.ArgumentParser(
        prog="python -m hinge",
        description="Compute HINGE interaction diagrams from the original text input format.",
    )
    parser.add_argument("input_file", type=Path, nargs="?")
    parser.add_argument("output_file", type=Path, nargs="?")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open the desktop GUI.",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        help="Save an interaction-diagram plot, for example diagram.png or diagram.svg.",
    )
    args = parser.parse_args()
    if args.gui:
        return gui_main()
    if args.input_file is None:
        parser.error("input_file is required unless --gui is used")

    method, n, values = parse_input(args.input_file)
    diagram = compute_diagram(method, n, values)
    output = render_output(diagram)

    if args.output_file is None:
        print(output, end="")
    else:
        args.output_file.write_text(output, encoding="cp1250")
    if args.plot is not None:
        plot_diagram(diagram, args.plot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
