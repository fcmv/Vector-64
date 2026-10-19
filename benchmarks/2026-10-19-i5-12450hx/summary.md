# Collected benchmark results

Source: `85369956e82b82f1bba57b15d67a654f7ec14012`.

Canary baseline: 6,396,476 NPS; tolerance: +/-5.0%.
Rejected attempts retained: 2.
Accepted results below exclude warmups and rejected attempts.

Canary checks detect relative machine drift, not CPU temperature or an initially slow machine.

| Sample attempt | Accepted | Before drift % | After drift % | Reason |
|---|---|---:|---:|---|
| warmup-1-classical #1 | True | -1.59 | -0.85 | ok |
| warmup-1-nnue #1 | True | +0.22 | -0.22 | ok |
| warmup-1-perft #1 | True | +0.65 | -0.11 | ok |
| run1-classical #1 | True | -0.43 | -1.59 | ok |
| run1-nnue #1 | True | -0.96 | -0.11 | ok |
| run1-perft #1 | True | -0.11 | -1.07 | ok |
| run2-nnue #1 | True | -1.07 | -2.83 | ok |
| run2-perft #1 | True | -0.54 | -0.96 | ok |
| run2-classical #1 | True | +0.22 | -0.96 | ok |
| run3-perft #1 | False | +0.87 | -8.21 | post_canary_drift |
| run3-perft #2 | False | -7.57 | - | pre_canary_drift |
| run3-perft #3 | True | -0.64 | -0.11 | ok |
| run3-classical #1 | True | -0.22 | +0.54 | ok |
| run3-nnue #1 | True | +0.87 | +0.87 | ok |
| run4-classical #1 | True | +0.11 | -0.11 | ok |
| run4-nnue #1 | True | -0.11 | -0.32 | ok |
| run4-perft #1 | True | +0.54 | +0.87 | ok |
| run5-nnue #1 | True | -1.17 | -0.64 | ok |
| run5-perft #1 | True | +0.98 | +0.00 | ok |
| run5-classical #1 | True | +0.98 | -1.07 | ok |

## classical

| Runs | Nodes | Median ms (min-max) | Median NPS (min-max) |
|---:|---:|---:|---:|
| 5 | 5,935,930 | 932 (922-937) | 6,369,023 (6,335,037-6,438,101) |

## nnue

| Runs | Nodes | Median ms (min-max) | Median NPS (min-max) |
|---:|---:|---:|---:|
| 5 | 2,704,705 | 1,419 (1,417-1,423) | 1,906,064 (1,900,706-1,908,754) |

## perft

| Position | Mode | Nodes | Median seconds (min-max) | Median reported MNPS |
|---|---|---:|---:|---:|
| 1 | Single | 4,865,609 | 0.017 (0.017-0.018) | 282 |
| 1 | Multi | 4,865,609 | 0.005 (0.005-0.006) | 954 |
| 2 | Single | 193,690,690 | 0.621 (0.619-0.629) | 311 |
| 2 | Multi | 193,690,690 | 0.107 (0.106-0.109) | 1805 |
| 3 | Single | 674,624 | 0.004 (0.004-0.004) | 161 |
| 3 | Multi | 674,624 | 0.002 (0.002-0.002) | 375 |
| 4 | Single | 15,833,292 | 0.067 (0.066-0.068) | 237 |
| 4 | Multi | 15,833,292 | 0.017 (0.016-0.019) | 928 |
| 5 | Single | 89,941,194 | 0.354 (0.351-0.359) | 254 |
| 5 | Multi | 89,941,194 | 0.060 (0.058-0.063) | 1494 |
| 6 | Single | 164,075,551 | 0.508 (0.504-0.512) | 322 |
| 6 | Multi | 164,075,551 | 0.086 (0.085-0.088) | 1908 |

Perft seconds are rounded to three decimals; reported MNPS is truncated.
Multi perft uses one task per legal root move, not a fixed-size search pool.

