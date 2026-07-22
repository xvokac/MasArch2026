# MELB external load spreading check

Implemented `Q_CODE` variants from `cal_live_load`:

- `Q_CODE=0`: point load without spreading
- `Q_CODE=1`: uniform spreading through fill height below the load
- `Q_CODE=2`: non-uniform Boussinesq spreading

No preserved MELB output file with `Q_CODE=1` or `Q_CODE=2` was found in the project tree. The checks therefore use `D:\Documents\2026\MASARCH2026\Melbourne\TEST.IN` as a base input and change only `Q_CODE`, with lateral soil pressure disabled for isolation.

## Synthetic checks

| Q_CODE | load on arch | nonzero loaded blocks | final load factor |
|---:|---:|---:|---:|
| 1 | 1.000000 | 9 | 64.678028 |
| 2 | 0.876341 | 10 | 70.915668 |

For `Q_CODE=2`, part of the Boussinesq load is accounted as spreading beyond the supports (`LHS/RHS`) exactly as in the original MELB logic, so the load integrated over arch blocks can be smaller than the input load.

Regression status:

- unit tests cover both `Q_CODE=1` and `Q_CODE=2`
- existing `Q_CODE=0` corpus remains unchanged
