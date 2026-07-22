from __future__ import annotations

import argparse
from pathlib import Path

from .core import format_equilibrium_diagnostic, format_model_report, format_moment_only_diagnostic, read_model


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m arch_lbt",
        description="Run ArchLBT GUI or prepare a lower-bound report from an input file.",
    )
    parser.add_argument("input_file", type=Path, nargs="?")
    parser.add_argument("output_file", type=Path, nargs="?")
    parser.add_argument(
        "--diagnose-equilibrium",
        action="store_true",
        help="Run only the equilibrium mapping diagnostic, without strength limits.",
    )
    parser.add_argument(
        "--diagnose-moment-only",
        action="store_true",
        help="Run only moment-domain limits abs(M) <= N*D/2, without standalone N >= 0.",
    )
    args = parser.parse_args()

    if args.input_file is None:
        from .gui import main as gui_main

        return gui_main()

    model = read_model(args.input_file)
    if args.diagnose_equilibrium and args.diagnose_moment_only:
        parser.error("choose only one diagnostic mode")
    if args.diagnose_equilibrium:
        report = format_equilibrium_diagnostic(model)
    elif args.diagnose_moment_only:
        report = format_moment_only_diagnostic(model)
    else:
        report = format_model_report(model)
    if args.output_file is None:
        print(report, end="")
    else:
        args.output_file.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
