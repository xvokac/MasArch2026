# MELB / MasArch Regression Corpus

This folder does not implement `MELB.exe` yet. It captures the preserved
`zlamal*.in` / output files as a regression corpus for the future Python port.
It also contains small parsers for preserved MELB work files:

- `*.AB`: transformation matrix dump, read as `4*(N+1)` by `3*(N+1)` float32 values
- `*.sim`: simplex dump header/table candidates from the old Numerical Recipes solver
- `*.txt` / detailed output: geometry, loads, transformed loads, and result vectors

The `zlamal*.in` inputs use the later `MELB.exe` / `MasArch.exe` format, not the
older `MArch.exe` input format.

Run:

```powershell
python -m unittest discover -s tests
```

Run the PySide6 desktop GUI:

```powershell
cd C:\Users\Vokac\Documents\Codex\2026-07-10\jak\melb_regression
python -m melb_regression
```

The PySide6 GUI opens, edits, creates, and saves MELB `*.in` files through a
form, runs the Python solver, shows summary/result tables, plots the arch with
active hinges and the normal-force line, and exports Python-generated `txt/out`
files.

Current corpus summary:

- 112 parsed `zlamal*.in` cases
- 106 preserved output files with parseable `icase` and `lambda`
- `d_CODE` distribution: `0:14`, `1:14`, `2:14`, `3:14`, `4:56`
- all preserved parsed results currently have `icase=0`
- reference `zlamal0_1.AB` shape: `164 x 123` for `N=40`
- reference `zlamal0_1.txt` detail table shapes are covered by regression tests
- `AB @ transformed_loads_from_txt` is checked against the preserved `.sim` rows
- the `.sim` objective coefficients reproduce the historical `lambda` when dotted
  with the preserved active local deformation vector
- a SciPy/HiGHS `linprog` static-dual model reproduces `zlamal0_1`:
  `lambda`, active hinge indices, and local deformation multipliers
