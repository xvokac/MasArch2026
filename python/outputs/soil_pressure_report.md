# MELB lateral soil pressure check

Reference case: `D:\Documents\2026\MASARCH2026\Melbourne\TEST.IN`

This is the preserved test case for `K_CODE = 2`, i.e. recalculation of lateral soil pressure after the first mechanism is found.

## Result

| quantity | generated | preserved | difference |
|---|---:|---:|---:|
| first load factor | 38.0122015 | 38.0111890 | 0.0010125 |
| final load factor after soil-pressure recalculation | 43.5571745 | 43.5565340 | 0.0006405 |

Additional checks:

- recalculated fill-load table max difference: `3.02e-6`
- recalculated external-load table max difference: `3.64e-7`
- final `test.sim` max value difference: `2.29e-5`

The first fill-load row is treated as active pressure when its computed displacement is numerically zero. This matches the preserved MELB output and old float behavior for `TEST.IN`.
