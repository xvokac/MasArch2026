from __future__ import annotations

import argparse
from pathlib import Path

from arch_lbt import lbt_input_from_melb, write_arch_lbt_input

try:
    from melb_regression.melb_regression import read_melb_input
except ImportError:
    from melb_regression import read_melb_input


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert MELB klenba_*.in files to the simpler ArchLBT input format.")
    parser.add_argument("--input-dir", type=Path, default=Path.cwd(), help="Directory with source klenba_*.in files.")
    parser.add_argument("--pattern", default="klenba_[0-9].in", help="Source glob pattern.")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd(), help="Directory for *_lbt.in files.")
    parser.add_argument("--friction", type=float, default=0.1, help="Friction coefficient written to every LBT file.")
    args = parser.parse_args()

    input_paths = sorted(args.input_dir.glob(args.pattern))
    if not input_paths:
        raise SystemExit(f"No files matched {args.input_dir / args.pattern}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for input_path in input_paths:
        output_path = args.output_dir / f"{input_path.stem}_lbt.in"
        data = read_melb_input(input_path)
        lbt_data = lbt_input_from_melb(data, friction_coefficient=args.friction, path=output_path)
        write_arch_lbt_input(lbt_data, output_path)
        print(f"{input_path.name} -> {output_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
