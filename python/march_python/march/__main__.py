from __future__ import annotations

import argparse
from pathlib import Path

from .core import analyze, parse_input, render_output
from .plotting import plot_arch


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m march",
        description="Run the MArch masonry arch limit-analysis calculation.",
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_file", type=Path, nargs="?")
    parser.add_argument(
        "--list",
        action="store_true",
        help="Include per-generated mechanism rows, like the old list=Y option.",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        help="Save a plot of intrados, extrados and pressure line, for example arch.png or arch.svg.",
    )
    args = parser.parse_args()

    data = parse_input(args.input_file)
    result = analyze(data, list_generated=args.list)
    output = render_output(result, args.input_file.name, include_generated=args.list)

    if args.output_file is None:
        print(output, end="")
    else:
        args.output_file.write_text(output, encoding="cp1250")
    if args.plot is not None:
        plot_arch(result, args.plot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
