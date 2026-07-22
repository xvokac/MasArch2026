# SciPy linprog corpus check

Input corpus: `D:\Documents\2026\MASARCH2026\masarch`

Checked complete cases with `txt + AB + sim`: 96

All 96 SciPy/HiGHS runs completed successfully.

## Summary by folder

| group | cases | active match | lambda <= 1e-4 | lambda <= 1e-3 | lambda <= 1e-2 | max lambda diff |
|---|---:|---:|---:|---:|---:|---:|
| zlamal0 | 12 | 9 | 7 | 9 | 11 | 0.0434577502 |
| zlamal1 | 12 | 11 | 7 | 11 | 11 | 0.0125890381 |
| zlamal2 | 12 | 11 | 4 | 11 | 11 | 0.0121853029 |
| zlamal3 | 12 | 11 | 8 | 11 | 11 | 0.0131430941 |
| zlamal4 | 12 | 11 | 5 | 11 | 11 | 0.0126866857 |
| zlamal5 | 12 | 11 | 8 | 11 | 11 | 0.0132393290 |
| zlamal6 | 12 | 11 | 5 | 11 | 11 | 0.0138099416 |
| zlamal7 | 12 | 7 | 4 | 7 | 10 | 0.0214712828 |

## Notes

- The model now compares against the final result block in iterative `txt` outputs.
- `zlamal2` now includes the Crisfield & Packham dissipated-work correction from `crush.h` (`cal_dis` / `modif_a_dis`), with the sign mapped to the SciPy/HiGHS dual formulation.
- Detailed per-case results are in `linprog_corpus_results.csv`.
