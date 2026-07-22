# ArchLBT

Lower-bound theorem sandbox for masonry arch limit analysis.

This package reuses verified MELB/MasArch geometry and load preparation
internally, but the preferred input file is now the simpler ArchLBT format
`*_lbt.in`.

- arch geometry: intrados, extrados, local coordinates
- permanent arch self-weight
- backfill load
- variable/surface load

The lower-bound direction is static: the model works with statically
admissible internal resultants `N`, `M`, and `T`, not with a kinematic collapse
mechanism.

Current solver:

- assembles resultants from one arch end,
- uses `state = permanent + lambda * variable`,
- maximizes `lambda`,
- uses `arch_width` as the out-of-plane width of the analysed arch strip,
- enforces finite-strength parabolic interaction:
  - `0 <= N <= fc*b*D`
  - `abs(M) <= N*(D/2 - N/(2*fc*b))`
- enforces joint friction when `mu > 0`:
  - `abs(T) <= mu*N`

Run the GUI:

```powershell
cd D:\Documents\2026\MASARCH2026\python
python -m arch_lbt
```

Convert the original MELB-style `klenba_*.in` examples to ArchLBT inputs with
uniform friction coefficient `mu = 0.1`:

```powershell
python .\arch_lbt\convert_klenba_to_lbt.py --input-dir . --pattern klenba_[0-9].in --output-dir . --friction 0.1
```

Run a preparation/lower-bound report from a new LBT input:

```powershell
cd D:\Documents\2026\MASARCH2026\python
python -m arch_lbt klenba_1_lbt.in
```

The LBT input field `arch_width` is the width `b` of the arch strip. The old
unit-strip behaviour is `arch_width = 1`.

## Units and width convention

ArchLBT does not enforce physical units in code. Use one consistent
force-length unit system throughout the input. The intended convention is:

- geometry values such as `span`, `rise`, `thickness`, `fill_height`,
  `point_load` position and width: length units, typically `m`;
- `masonry_unit_weight` and `fill_unit_weight`: force per volume, typically
  `kN/m3`;
- `point_load` force value: total surface load force `F` acting on the loaded
  length, already including the out-of-plane arch width, typically `kN`;
- `arch_width`: out-of-plane width `b` of the analysed arch strip, typically
  `m`;
- `compression_strength`: force per area consistent with the chosen units,
  e.g. `kN/m2` when forces are in `kN` and lengths in `m`.

The prepared self-weight and fill load are interpreted first for a 1 m wide
strip and are then multiplied internally by `arch_width`. The `point_load`
force is already a total force for the analysed strip and is not multiplied by
`arch_width` again. The interaction diagram uses the same width:

```text
Nmax = fc * arch_width * D
```

## Geometry options

The base intrados shape is selected by `geom_code`:

- `geom_code = 1`: circular intrados;
- `geom_code = 2`: parabolic intrados.

The extrados/block generation is selected by `extrados_mode`:

- `normal`: original behaviour, extrados follows the intrados with constant
  normal thickness `D`;
- `horizontal`: new behaviour, extrados is a horizontal line at
  `rise + thickness`; block joint lines connect intrados points to this flat
  extrados.
- `horizontal_width_radial_joints`: horizontal extrados at `rise + thickness`,
  but each joint follows the intrados normal/radial direction. The top surface
  is therefore wider than the intrados.

Write the report to a file:

```powershell
python -m arch_lbt klenba_1_lbt.in arch_lbt_report.txt
```

Generate batch reports and plots:

```powershell
python .\arch_lbt\batch_klenba_lbt.py
```

Run tests:

```powershell
python -m unittest discover -s arch_lbt\tests
```
