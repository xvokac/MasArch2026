# MasArch2026

Archive and Python reconstruction workspace for masonry arch limit analysis.

The repository contains preserved historical sources/examples and active Python
ports used for checking and extending the calculations.

## Main Areas

- `MArch/`, `Melbourne/`, `hinge/`, `masarch/`: preserved historical programs,
  inputs, and reference outputs.
- `python/arch_lbt`: lower-bound theorem analysis with GUI, batch processing,
  geometry plots, M-N interaction checks, N-T shear/friction checks, and PDF
  export.
- `python/melb_regression`: regression corpus and Python reconstruction helpers
  for MELB/MasArch.
- `python/hinge_python`: Python port of the HINGE interaction-diagram
  calculator.
- `python/march_python`: Python port/regression workspace for the MArch
  mechanism-based calculator.

## Useful Commands

Run the ArchLBT GUI:

```powershell
cd D:\Documents\2026\MASARCH2026\python
python -m arch_lbt
```

Run an ArchLBT input:

```powershell
cd D:\Documents\2026\MASARCH2026\python
python -m arch_lbt klenba_1_lbt.in
```

Run Python regression tests:

```powershell
cd D:\Documents\2026\MASARCH2026\python
python -m unittest discover -s .\arch_lbt\tests

cd D:\Documents\2026\MASARCH2026\python\hinge_python
python -m unittest discover -s tests

cd D:\Documents\2026\MASARCH2026\python\march_python
python -m unittest discover -s tests

cd D:\Documents\2026\MASARCH2026\python\melb_regression
python -m unittest discover -s tests
```

Generated plots, reports, scratch probes, and Python cache files are ignored by
Git. Source code, preserved examples, package README files, and input files are
kept under version control.
