# HINGE Python

Python port of the original `HINGE.exe` interaction-diagram calculator.

The input format is intentionally compatible with the old text files:

```text
first line is a comment
METHOD
N
method-specific numeric values...
```

Run:

```powershell
python -m hinge D:\Documents\2026\MASARCH2026\hinge\pokus2.txt pokus2.out
```

Run the PySide6 desktop GUI:

```powershell
cd D:\Documents\2026\MASARCH2026\python\hinge_python
python -m hinge
```

Save a graph too:

```powershell
python -m hinge D:\Documents\2026\MASARCH2026\hinge\pokus2.txt pokus2.out --plot pokus2.png
```

Run regression tests against the original examples:

```powershell
python -m unittest discover -s tests
```
