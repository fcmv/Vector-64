# Collected benchmark results

Source: `85369956e82b82f1bba57b15d67a654f7ec14012`.

Canary baseline: 6,396,476 NPS; tolerance: +/-5.0%.
Rejected attempts retained: 10.
Accepted results below exclude warmups and rejected attempts.

Canary checks detect relative machine drift, not CPU temperature or an initially slow machine.

| Sample attempt | Accepted | Before drift % | After drift % | Reason |
|---|---|---:|---:|---|
| warmup-1-classical-d13-t1-h8-pv1 #1 | True | -2.21 | -2.83 | ok |
| warmup-1-nnue-d13-t1-h8-pv1 #1 | False | -6.45 | - | pre_canary_drift |
| warmup-1-nnue-d13-t1-h8-pv1 #2 | True | -2.73 | -0.85 | ok |
| warmup-1-classical-d8-t1-h8-pv1 #1 | True | -3.33 | -1.59 | ok |
| warmup-1-nnue-d8-t1-h8-pv1 #1 | True | -0.75 | -1.80 | ok |
| warmup-1-classical-d10-t1-h8-pv1 #1 | True | -1.69 | -2.93 | ok |
| warmup-1-nnue-d10-t1-h8-pv1 #1 | True | -1.17 | -0.85 | ok |
| warmup-1-classical-d12-t1-h8-pv1 #1 | True | -3.13 | -0.64 | ok |
| warmup-1-nnue-d12-t1-h8-pv1 #1 | True | -3.73 | -1.38 | ok |
| warmup-1-classical-d14-t1-h8-pv1 #1 | True | -1.80 | +0.43 | ok |
| warmup-1-nnue-d14-t1-h8-pv1 #1 | True | +1.09 | -0.75 | ok |
| warmup-1-classical-d16-t1-h8-pv1 #1 | True | +0.43 | -1.59 | ok |
| warmup-1-nnue-d16-t1-h8-pv1 #1 | True | -2.62 | -1.59 | ok |
| warmup-1-classical-d13-t2-h8-pv1 #1 | True | +0.11 | -1.07 | ok |
| warmup-1-nnue-d13-t2-h8-pv1 #1 | False | -12.20 | - | pre_canary_drift |
| warmup-1-nnue-d13-t2-h8-pv1 #2 | True | +0.65 | -2.21 | ok |
| warmup-1-classical-d13-t4-h8-pv1 #1 | True | -1.49 | -0.22 | ok |
| warmup-1-nnue-d13-t4-h8-pv1 #1 | True | -0.85 | -0.64 | ok |
| warmup-1-classical-d13-t8-h8-pv1 #1 | True | -1.38 | +1.31 | ok |
| warmup-1-nnue-d13-t8-h8-pv1 #1 | True | -0.75 | +0.00 | ok |
| warmup-1-classical-d13-t12-h8-pv1 #1 | True | -1.28 | -0.43 | ok |
| warmup-1-nnue-d13-t12-h8-pv1 #1 | True | -0.32 | -1.49 | ok |
| warmup-1-classical-d13-t1-h64-pv1 #1 | True | -0.96 | +1.20 | ok |
| warmup-1-nnue-d13-t1-h64-pv1 #1 | True | +0.22 | -0.32 | ok |
| warmup-1-classical-d13-t1-h256-pv1 #1 | True | +0.11 | -0.64 | ok |
| warmup-1-nnue-d13-t1-h256-pv1 #1 | True | -2.52 | -1.80 | ok |
| warmup-1-classical-d13-t1-h8-pv3 #1 | True | -0.64 | +0.43 | ok |
| warmup-1-nnue-d13-t1-h8-pv3 #1 | False | -1.28 | -17.07 | post_canary_drift |
| warmup-1-nnue-d13-t1-h8-pv3 #2 | False | -13.91 | - | pre_canary_drift |
| warmup-1-nnue-d13-t1-h8-pv3 #3 | True | -0.32 | +0.11 | ok |
| warmup-1-classical-d13-t1-h8-pv5 #1 | True | -0.32 | -0.75 | ok |
| warmup-1-nnue-d13-t1-h8-pv5 #1 | True | +0.87 | -0.43 | ok |
| warmup-1-perft #1 | True | +0.00 | +0.22 | ok |
| run1-classical-d13-t1-h8-pv1 #1 | True | -0.32 | -0.85 | ok |
| run1-nnue-d13-t1-h8-pv1 #1 | True | +0.65 | +0.00 | ok |
| run1-classical-d8-t1-h8-pv1 #1 | True | -3.03 | -0.75 | ok |
| run1-nnue-d8-t1-h8-pv1 #1 | False | -1.49 | -13.19 | post_canary_drift |
| run1-nnue-d8-t1-h8-pv1 #2 | True | -1.90 | -0.22 | ok |
| run1-classical-d10-t1-h8-pv1 #1 | True | +0.32 | +0.00 | ok |
| run1-nnue-d10-t1-h8-pv1 #1 | True | +0.32 | -2.11 | ok |
| run1-classical-d12-t1-h8-pv1 #1 | True | -1.38 | -0.43 | ok |
| run1-nnue-d12-t1-h8-pv1 #1 | True | -0.96 | -1.59 | ok |
| run1-classical-d14-t1-h8-pv1 #1 | True | -1.07 | -0.11 | ok |
| run1-nnue-d14-t1-h8-pv1 #1 | True | +0.43 | -2.21 | ok |
| run1-classical-d16-t1-h8-pv1 #1 | True | -1.07 | -1.38 | ok |
| run1-nnue-d16-t1-h8-pv1 #1 | True | -1.07 | -0.75 | ok |
| run1-classical-d13-t2-h8-pv1 #1 | True | -1.28 | -2.42 | ok |
| run1-nnue-d13-t2-h8-pv1 #1 | True | -1.69 | -0.64 | ok |
| run1-classical-d13-t4-h8-pv1 #1 | True | +0.32 | -1.59 | ok |
| run1-nnue-d13-t4-h8-pv1 #1 | False | -0.11 | -6.36 | post_canary_drift |
| run1-nnue-d13-t4-h8-pv1 #2 | True | -1.07 | -3.93 | ok |
| run1-classical-d13-t8-h8-pv1 #1 | True | -1.49 | +0.22 | ok |
| run1-nnue-d13-t8-h8-pv1 #1 | True | +0.00 | -1.38 | ok |
| run1-classical-d13-t12-h8-pv1 #1 | True | +0.32 | +0.32 | ok |
| run1-nnue-d13-t12-h8-pv1 #1 | True | +1.75 | +0.22 | ok |
| run1-classical-d13-t1-h64-pv1 #1 | True | -1.28 | -0.43 | ok |
| run1-nnue-d13-t1-h64-pv1 #1 | True | +0.11 | -2.52 | ok |
| run1-classical-d13-t1-h256-pv1 #1 | True | -0.96 | -0.75 | ok |
| run1-nnue-d13-t1-h256-pv1 #1 | True | -1.90 | +0.54 | ok |
| run1-classical-d13-t1-h8-pv3 #1 | True | +0.98 | -0.43 | ok |
| run1-nnue-d13-t1-h8-pv3 #1 | True | -1.69 | -0.85 | ok |
| run1-classical-d13-t1-h8-pv5 #1 | True | -0.85 | +1.53 | ok |
| run1-nnue-d13-t1-h8-pv5 #1 | True | -0.22 | -0.64 | ok |
| run1-perft #1 | True | +0.87 | -0.22 | ok |
| run2-nnue-d13-t1-h8-pv1 #1 | False | -0.32 | -6.64 | post_canary_drift |
| run2-nnue-d13-t1-h8-pv1 #2 | True | -3.03 | -0.43 | ok |
| run2-classical-d8-t1-h8-pv1 #1 | True | -0.96 | -1.07 | ok |
| run2-nnue-d8-t1-h8-pv1 #1 | True | -1.28 | -1.90 | ok |
| run2-classical-d10-t1-h8-pv1 #1 | True | -1.28 | -0.22 | ok |
| run2-nnue-d10-t1-h8-pv1 #1 | True | +0.22 | +1.42 | ok |
| run2-classical-d12-t1-h8-pv1 #1 | True | -1.28 | +0.54 | ok |
| run2-nnue-d12-t1-h8-pv1 #1 | True | -0.11 | +1.09 | ok |
| run2-classical-d14-t1-h8-pv1 #1 | True | -1.28 | -1.17 | ok |
| run2-nnue-d14-t1-h8-pv1 #1 | True | +1.09 | -0.54 | ok |
| run2-classical-d16-t1-h8-pv1 #1 | True | +0.32 | +0.43 | ok |
| run2-nnue-d16-t1-h8-pv1 #1 | True | -2.21 | -0.96 | ok |
| run2-classical-d13-t2-h8-pv1 #1 | True | -2.21 | -0.96 | ok |
| run2-nnue-d13-t2-h8-pv1 #1 | True | -1.59 | -0.64 | ok |
| run2-classical-d13-t4-h8-pv1 #1 | True | -1.90 | -0.96 | ok |
| run2-nnue-d13-t4-h8-pv1 #1 | True | +0.11 | +0.87 | ok |
| run2-classical-d13-t8-h8-pv1 #1 | True | -1.80 | -0.96 | ok |
| run2-nnue-d13-t8-h8-pv1 #1 | False | -1.28 | -6.64 | post_canary_drift |
| run2-nnue-d13-t8-h8-pv1 #2 | True | -1.07 | -0.75 | ok |
| run2-classical-d13-t12-h8-pv1 #1 | True | -0.22 | -0.96 | ok |
| run2-nnue-d13-t12-h8-pv1 #1 | True | -0.75 | -2.62 | ok |
| run2-classical-d13-t1-h64-pv1 #1 | True | -1.80 | -0.22 | ok |
| run2-nnue-d13-t1-h64-pv1 #1 | True | +0.76 | +0.98 | ok |
| run2-classical-d13-t1-h256-pv1 #1 | True | +0.22 | +0.00 | ok |
| run2-nnue-d13-t1-h256-pv1 #1 | True | +0.11 | +0.87 | ok |
| run2-classical-d13-t1-h8-pv3 #1 | True | -1.38 | +0.11 | ok |
| run2-nnue-d13-t1-h8-pv3 #1 | True | -2.83 | +1.31 | ok |
| run2-classical-d13-t1-h8-pv5 #1 | True | +0.11 | +0.32 | ok |
| run2-nnue-d13-t1-h8-pv5 #1 | True | -1.07 | -1.49 | ok |
| run2-perft #1 | True | -0.22 | -0.22 | ok |
| run2-classical-d13-t1-h8-pv1 #1 | True | -1.49 | +0.76 | ok |
| run3-classical-d8-t1-h8-pv1 #1 | True | +0.00 | -0.64 | ok |
| run3-nnue-d8-t1-h8-pv1 #1 | True | -2.52 | -0.75 | ok |
| run3-classical-d10-t1-h8-pv1 #1 | True | -0.43 | -0.32 | ok |
| run3-nnue-d10-t1-h8-pv1 #1 | True | -1.28 | -0.11 | ok |
| run3-classical-d12-t1-h8-pv1 #1 | True | +0.11 | -0.22 | ok |
| run3-nnue-d12-t1-h8-pv1 #1 | True | +0.43 | +0.32 | ok |
| run3-classical-d14-t1-h8-pv1 #1 | True | +1.31 | +0.43 | ok |
| run3-nnue-d14-t1-h8-pv1 #1 | True | +1.31 | +0.22 | ok |
| run3-classical-d16-t1-h8-pv1 #1 | True | +0.32 | -0.22 | ok |
| run3-nnue-d16-t1-h8-pv1 #1 | True | +0.32 | +0.98 | ok |
| run3-classical-d13-t2-h8-pv1 #1 | True | -0.54 | +1.42 | ok |
| run3-nnue-d13-t2-h8-pv1 #1 | True | -0.64 | -0.75 | ok |
| run3-classical-d13-t4-h8-pv1 #1 | True | -1.17 | -1.59 | ok |
| run3-nnue-d13-t4-h8-pv1 #1 | True | -2.73 | -0.32 | ok |
| run3-classical-d13-t8-h8-pv1 #1 | True | -0.54 | -2.21 | ok |
| run3-nnue-d13-t8-h8-pv1 #1 | False | -0.64 | -6.64 | post_canary_drift |
| run3-nnue-d13-t8-h8-pv1 #2 | True | -1.90 | -0.75 | ok |
| run3-classical-d13-t12-h8-pv1 #1 | True | -0.54 | +1.75 | ok |
| run3-nnue-d13-t12-h8-pv1 #1 | True | +1.53 | -1.49 | ok |
| run3-classical-d13-t1-h64-pv1 #1 | True | -2.52 | -0.11 | ok |
| run3-nnue-d13-t1-h64-pv1 #1 | True | -1.38 | -0.32 | ok |
| run3-classical-d13-t1-h256-pv1 #1 | True | +0.43 | +0.98 | ok |
| run3-nnue-d13-t1-h256-pv1 #1 | True | -0.43 | -0.96 | ok |
| run3-classical-d13-t1-h8-pv3 #1 | True | +1.42 | -1.07 | ok |
| run3-nnue-d13-t1-h8-pv3 #1 | True | -0.64 | -0.54 | ok |
| run3-classical-d13-t1-h8-pv5 #1 | True | +0.22 | +0.76 | ok |
| run3-nnue-d13-t1-h8-pv5 #1 | True | -0.22 | -0.54 | ok |
| run3-perft #1 | True | -0.43 | +0.32 | ok |
| run3-classical-d13-t1-h8-pv1 #1 | True | +1.31 | -0.54 | ok |
| run3-nnue-d13-t1-h8-pv1 #1 | True | +1.09 | -1.69 | ok |
| run4-nnue-d8-t1-h8-pv1 #1 | False | -6.45 | - | pre_canary_drift |
| run4-nnue-d8-t1-h8-pv1 #2 | True | -0.75 | -0.54 | ok |
| run4-classical-d10-t1-h8-pv1 #1 | True | -0.54 | -0.54 | ok |
| run4-nnue-d10-t1-h8-pv1 #1 | True | +0.00 | -1.69 | ok |
| run4-classical-d12-t1-h8-pv1 #1 | True | -1.80 | -0.11 | ok |
| run4-nnue-d12-t1-h8-pv1 #1 | True | -0.11 | -0.11 | ok |
| run4-classical-d14-t1-h8-pv1 #1 | True | +1.09 | +0.11 | ok |
| run4-nnue-d14-t1-h8-pv1 #1 | True | -0.43 | -0.64 | ok |
| run4-classical-d16-t1-h8-pv1 #1 | True | -0.11 | -0.85 | ok |
| run4-nnue-d16-t1-h8-pv1 #1 | True | +0.11 | -0.43 | ok |
| run4-classical-d13-t2-h8-pv1 #1 | True | +1.20 | -0.64 | ok |
| run4-nnue-d13-t2-h8-pv1 #1 | True | -0.64 | -1.28 | ok |
| run4-classical-d13-t4-h8-pv1 #1 | True | +0.00 | -0.22 | ok |
| run4-nnue-d13-t4-h8-pv1 #1 | True | +0.43 | -1.07 | ok |
| run4-classical-d13-t8-h8-pv1 #1 | True | -1.17 | +1.75 | ok |
| run4-nnue-d13-t8-h8-pv1 #1 | True | -0.64 | -0.85 | ok |
| run4-classical-d13-t12-h8-pv1 #1 | True | -0.32 | -2.21 | ok |
| run4-nnue-d13-t12-h8-pv1 #1 | True | +0.76 | -1.38 | ok |
| run4-classical-d13-t1-h64-pv1 #1 | True | -0.32 | -2.21 | ok |
| run4-nnue-d13-t1-h64-pv1 #1 | True | +0.11 | +0.43 | ok |
| run4-classical-d13-t1-h256-pv1 #1 | True | +0.11 | +0.65 | ok |
| run4-nnue-d13-t1-h256-pv1 #1 | True | -1.80 | -0.54 | ok |
| run4-classical-d13-t1-h8-pv3 #1 | True | -0.75 | -0.75 | ok |
| run4-nnue-d13-t1-h8-pv3 #1 | True | -2.93 | +0.00 | ok |
| run4-classical-d13-t1-h8-pv5 #1 | True | +0.22 | +0.32 | ok |
| run4-nnue-d13-t1-h8-pv5 #1 | True | +0.00 | +0.54 | ok |
| run4-perft #1 | True | -0.54 | -0.11 | ok |
| run4-classical-d13-t1-h8-pv1 #1 | True | -1.28 | -0.22 | ok |
| run4-nnue-d13-t1-h8-pv1 #1 | True | -0.75 | -0.32 | ok |
| run4-classical-d8-t1-h8-pv1 #1 | True | +0.76 | +0.22 | ok |
| run5-classical-d10-t1-h8-pv1 #1 | True | -0.32 | -0.64 | ok |
| run5-nnue-d10-t1-h8-pv1 #1 | True | +0.22 | -0.75 | ok |
| run5-classical-d12-t1-h8-pv1 #1 | True | -0.85 | -2.32 | ok |
| run5-nnue-d12-t1-h8-pv1 #1 | True | +1.42 | +0.54 | ok |
| run5-classical-d14-t1-h8-pv1 #1 | True | -0.85 | +1.31 | ok |
| run5-nnue-d14-t1-h8-pv1 #1 | True | -0.64 | +0.87 | ok |
| run5-classical-d16-t1-h8-pv1 #1 | True | -0.75 | +1.53 | ok |
| run5-nnue-d16-t1-h8-pv1 #1 | True | -0.32 | -1.28 | ok |
| run5-classical-d13-t2-h8-pv1 #1 | True | -0.54 | -1.17 | ok |
| run5-nnue-d13-t2-h8-pv1 #1 | True | -1.07 | -0.11 | ok |
| run5-classical-d13-t4-h8-pv1 #1 | True | +0.00 | -0.43 | ok |
| run5-nnue-d13-t4-h8-pv1 #1 | True | -0.64 | -2.52 | ok |
| run5-classical-d13-t8-h8-pv1 #1 | True | -0.22 | -1.07 | ok |
| run5-nnue-d13-t8-h8-pv1 #1 | True | -1.69 | -0.64 | ok |
| run5-classical-d13-t12-h8-pv1 #1 | True | -1.69 | -0.54 | ok |
| run5-nnue-d13-t12-h8-pv1 #1 | True | -0.85 | +1.09 | ok |
| run5-classical-d13-t1-h64-pv1 #1 | True | +0.22 | +0.00 | ok |
| run5-nnue-d13-t1-h64-pv1 #1 | True | -2.73 | -0.85 | ok |
| run5-classical-d13-t1-h256-pv1 #1 | True | +0.54 | -0.32 | ok |
| run5-nnue-d13-t1-h256-pv1 #1 | True | +0.32 | -2.21 | ok |
| run5-classical-d13-t1-h8-pv3 #1 | True | -1.49 | +0.87 | ok |
| run5-nnue-d13-t1-h8-pv3 #1 | True | -1.38 | +0.22 | ok |
| run5-classical-d13-t1-h8-pv5 #1 | True | -0.96 | +0.54 | ok |
| run5-nnue-d13-t1-h8-pv5 #1 | True | -0.96 | -0.96 | ok |
| run5-perft #1 | True | -0.85 | -1.59 | ok |
| run5-classical-d13-t1-h8-pv1 #1 | True | -0.85 | -3.63 | ok |
| run5-nnue-d13-t1-h8-pv1 #1 | True | +0.22 | -0.96 | ok |
| run5-classical-d8-t1-h8-pv1 #1 | True | -1.07 | +0.32 | ok |
| run5-nnue-d8-t1-h8-pv1 #1 | True | +0.11 | +0.43 | ok |

## perft

| Position | Mode | Nodes | Median seconds (min-max) | Median reported MNPS |
|---|---|---:|---:|---:|
| 1 | Single | 4,865,609 | 0.017 (0.017-0.018) | 287 |
| 1 | Multi | 4,865,609 | 0.005 (0.005-0.005) | 942 |
| 2 | Single | 193,690,690 | 0.620 (0.620-0.628) | 312 |
| 2 | Multi | 193,690,690 | 0.110 (0.106-0.115) | 1762 |
| 3 | Single | 674,624 | 0.004 (0.004-0.004) | 156 |
| 3 | Multi | 674,624 | 0.003 (0.002-0.003) | 248 |
| 4 | Single | 15,833,292 | 0.067 (0.066-0.068) | 237 |
| 4 | Multi | 15,833,292 | 0.018 (0.016-0.021) | 899 |
| 5 | Single | 89,941,194 | 0.348 (0.347-0.356) | 258 |
| 5 | Multi | 89,941,194 | 0.060 (0.059-0.063) | 1494 |
| 6 | Single | 164,075,551 | 0.507 (0.505-0.510) | 323 |
| 6 | Multi | 164,075,551 | 0.090 (0.087-0.090) | 1833 |

Perft seconds are rounded to three decimals; reported MNPS is truncated.
Multi perft uses one task per legal root move, not a fixed-size search pool.


## Fixed-depth search matrix

| Profile | Runs | Nodes median (min-max) | Time ms median (min-max) | NPS median (min-max) |
|---|---:|---:|---:|---:|
| classical-d13-t1-h8-pv1 | 5 | 5,935,930 (5,935,930-5,935,930) | 931 (927-936) | 6,375,864 (6,341,805-6,403,376) |
| nnue-d13-t1-h8-pv1 | 5 | 2,704,705 (2,704,705-2,704,705) | 1,422 (1,416-1,429) | 1,902,042 (1,892,725-1,910,102) |
| classical-d8-t1-h8-pv1 | 5 | 220,154 (220,154-220,154) | 33 (32-35) | 6,671,333 (6,290,114-6,879,812) |
| nnue-d8-t1-h8-pv1 | 5 | 134,250 (134,250-134,250) | 64 (63-66) | 2,097,656 (2,034,090-2,130,952) |
| classical-d10-t1-h8-pv1 | 5 | 1,140,187 (1,140,187-1,140,187) | 186 (181-188) | 6,130,037 (6,064,824-6,299,375) |
| nnue-d10-t1-h8-pv1 | 5 | 481,484 (481,484-481,484) | 245 (243-247) | 1,965,240 (1,949,327-1,981,415) |
| classical-d12-t1-h8-pv1 | 5 | 3,245,397 (3,245,397-3,245,397) | 508 (504-516) | 6,388,576 (6,289,529-6,439,279) |
| nnue-d12-t1-h8-pv1 | 5 | 1,414,396 (1,414,396-1,414,396) | 738 (738-745) | 1,916,525 (1,898,518-1,916,525) |
| classical-d14-t1-h8-pv1 | 5 | 11,325,264 (11,325,264-11,325,264) | 1,745 (1,734-1,792) | 6,490,122 (6,319,901-6,531,294) |
| nnue-d14-t1-h8-pv1 | 5 | 4,754,623 (4,754,623-4,754,623) | 2,507 (2,495-2,514) | 1,896,538 (1,891,258-1,905,660) |
| classical-d16-t1-h8-pv1 | 5 | 30,363,261 (30,363,261-30,363,261) | 4,649 (4,632-4,720) | 6,531,138 (6,432,894-6,555,108) |
| nnue-d16-t1-h8-pv1 | 5 | 15,035,962 (15,035,962-15,035,962) | 8,007 (7,987-8,046) | 1,877,852 (1,868,749-1,882,554) |
| classical-d13-t2-h8-pv1 | 5 | 5,881,529 (5,648,865-7,349,135) | 695 (620-898) | 8,421,444 (8,183,891-9,262,250) |
| nnue-d13-t2-h8-pv1 | 5 | 3,155,964 (3,090,723-3,591,959) | 1,215 (1,172-1,402) | 2,597,501 (2,562,024-2,691,519) |
| classical-d13-t4-h8-pv1 | 5 | 9,155,571 (8,146,961-9,682,191) | 489 (422-524) | 19,021,986 (17,278,071-19,305,594) |
| nnue-d13-t4-h8-pv1 | 5 | 4,901,402 (4,581,366-5,436,209) | 874 (795-964) | 5,639,220 (5,538,805-6,126,553) |
| classical-d13-t8-h8-pv1 | 5 | 11,352,078 (11,123,148-12,557,829) | 450 (431-529) | 25,179,355 (21,459,504-27,075,361) |
| nnue-d13-t8-h8-pv1 | 5 | 6,281,118 (5,859,231-7,035,041) | 886 (762-1,013) | 7,328,848 (6,944,759-7,689,279) |
| classical-d13-t12-h8-pv1 | 5 | 11,774,820 (11,223,444-13,591,240) | 426 (409-515) | 27,307,758 (26,390,757-28,271,386) |
| nnue-d13-t12-h8-pv1 | 5 | 7,383,552 (6,501,955-7,548,483) | 959 (824-1,056) | 7,714,309 (7,148,184-7,890,722) |
| classical-d13-t1-h64-pv1 | 5 | 6,006,270 (6,006,270-6,006,270) | 1,345 (1,340-1,356) | 4,465,628 (4,429,402-4,482,291) |
| nnue-d13-t1-h64-pv1 | 5 | 2,589,951 (2,589,951-2,589,951) | 1,385 (1,379-1,390) | 1,870,000 (1,863,274-1,878,137) |
| classical-d13-t1-h256-pv1 | 5 | 5,644,709 (5,644,709-5,644,709) | 1,309 (1,307-1,330) | 4,312,229 (4,244,142-4,318,828) |
| nnue-d13-t1-h256-pv1 | 5 | 2,589,951 (2,589,951-2,589,951) | 1,392 (1,382-1,395) | 1,860,596 (1,856,595-1,874,060) |
| classical-d13-t1-h8-pv3 | 5 | 19,362,016 (19,362,016-19,362,016) | 2,968 (2,958-3,016) | 6,523,590 (6,419,766-6,545,644) |
| nnue-d13-t1-h8-pv3 | 5 | 12,573,810 (12,573,810-12,573,810) | 6,643 (6,635-6,657) | 1,892,790 (1,888,810-1,895,073) |
| classical-d13-t1-h8-pv5 | 5 | 27,602,463 (27,602,463-27,602,463) | 4,208 (4,197-4,260) | 6,559,520 (6,479,451-6,576,712) |
| nnue-d13-t1-h8-pv5 | 5 | 19,856,733 (19,856,733-19,856,733) | 10,693 (10,657-10,712) | 1,856,984 (1,853,690-1,863,257) |

## Matrix interpretation

Each search label records depth (d), threads (t), hash MB (h) and MultiPV (pv).
Search samples use the built-in eight-position suite in a fresh process.
The engine clears search state once at suite start; positions share its evolving state.
Only d13-t1-h8-pv1 has a committed golden node count. Other single-thread
configurations are checked for repeat consistency, which is not independent correctness proof.
Threaded node counts can vary; compare time to depth and nodes as well as NPS.
These are fixed-depth and perft measurements, not fixed-node/time or Elo tests.
