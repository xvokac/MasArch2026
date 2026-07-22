# MELB iteration reconstruction check

Input corpus: `D:\Documents\2026\MASARCH2026\masarch`

Implemented iterative methods:

- `d_CODE=1`: Livesley
- `d_CODE=2`: Crisfield & Packham, including dissipated work correction
- `d_CODE=4`: user interaction diagram, using four-point interpolation matching `polint`

## Reference spot checks

| case | generated lambda sequence | preserved lambda sequence | final AB max diff | final sim max diff |
|---|---:|---:|---:|---:|
| `zlamal1\zlamal1_1` | 9.158869, 8.758228, 8.765262 | 9.158882, 8.758239, 8.765233 | 1.274049e-6 | 4.291534e-6 |
| `zlamal2\zlamal2_1` | 9.158869, 8.765323, 8.765156 | 9.158882, 8.765375, 8.765131 | 1.274049e-6 | 4.291534e-6 |
| `zlamal3\zlamal3_1` | 9.158869, 8.684635, 8.694459 | 9.158882, 8.684657, 8.694510 | 1.274049e-6 | 4.291534e-6 |

## Corpus summary

| d_CODE | cases | step-count match | final lambda <= 1e-4 | final lambda <= 1e-3 | max final lambda diff |
|---:|---:|---:|---:|---:|---:|
| 1 | 9 | 9 | 7 | 9 | 0.0001900984 |
| 2 | 9 | 9 | 4 | 9 | 0.0002319748 |
| 4 | 36 | 35 | 25 | 36 | 0.0002294921 |

`zlamal6\zlamal6_2` stops one iteration earlier in Python because the load-factor change falls just inside the historical `1e-2` tolerance. Its final load-factor difference is `8.173e-5`.
