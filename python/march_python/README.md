# MArch Python

Python port of the original `MArch.exe` Heyman masonry arch limit-analysis
calculator.

Run from this directory:

```powershell
python -m march D:\Documents\2026\MASARCH2026\MArch\in1.txt in1_py.out --list
```

Save a graph of the old AutoCAD line output:

```powershell
python -m march D:\Documents\2026\MASARCH2026\MArch\in1.txt in1_py.out --plot in1_arch.png
```

Run regression tests:

```powershell
python -m unittest discover -s tests
```

Current regression coverage:

- parses all preserved example inputs: `in1`, `in2`, `in3`, `input`, `klenba`,
  and `dukovany_in`
- runs a quick shortened calculation for every preserved input
- checks the original C `rand()` sequence used for generated mechanisms
- checks the full primary result for `in1`

Known gaps:

- `dukovany_in` is marked as an expected failure for primary-result parity.

Performance note:

- interval sums of vertical forces and moments are precomputed once per input,
  because the original algorithm queries the same load intervals many times
  during the hinge-iteration process.
