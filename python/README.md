# MasArch2026 Python

Python workspace for masonry arch analysis tools and regression checks.

## Packages

- `arch_lbt`: lower-bound theorem analysis for masonry arches, including GUI,
  batch processing, ArchLBT input files, geometry plots, M-N interaction plots,
  N-T friction checks, and PDF export.
- `melb_regression`: Python reconstruction/regression corpus for the historical
  MELB/MasArch workflow.
- `hinge_python`: Python port of the HINGE interaction-diagram calculator with
  GUI.
- `march_python`: Python port/regression workspace for the historical MArch
  mechanism-based calculator.

## Typical Commands

Run the ArchLBT GUI:

```powershell
python -m arch_lbt
```

Run an ArchLBT calculation:

```powershell
python -m arch_lbt klenba_1_lbt.in
```

Run ArchLBT tests:

```powershell
python -m unittest discover -s .\arch_lbt\tests
```

Run all package regression tests:

```powershell
python -m unittest discover -s .\arch_lbt\tests
python -m unittest discover -s .\melb_regression\tests
python -m unittest discover -s .\hinge_python\tests
python -m unittest discover -s .\march_python\tests
```

## Repository Hygiene

Generated reports, plots, batch outputs, scratch probes, and Python cache files
are intentionally ignored by Git. Source code, package README files, and input
files such as `klenba_*.in` and `*_lbt.in` are kept under version control.
