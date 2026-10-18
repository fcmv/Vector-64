# Benchmarks and search evidence

This is the method for interpreting and reproducing engine evidence. It does
not publish a newly measured Elo rating or reuse old branch-local numbers as
current results. The expected search fingerprints live in
[tools/bench_signature.txt](tools/bench_signature.txt).

## Four different measurements

| Measurement | Establishes | Does not establish |
|---|---|---|
| Perft/reference counts | Agreement on the legal move tree for covered positions/depths. | Search speed, full adjudication, or playing strength. |
| Bench fingerprint | Fixed-node regression identity for a defined search/net configuration. | A speed or Elo improvement. |
| Search/inference timing | Throughput/latency under recorded hardware and settings. | Better moves or universal performance. |
| Controlled match/SPRT | Evidence about relative playing strength for that experimental setup. | An absolute public rating or all time controls/variants. |

## Record a run

Record candidate/baseline commits and executable hashes, compiler/version/flags,
CPU/ISA/OS, network hashes, position/opening inputs, budgets, threads/hash,
reset/warmup procedure, repetitions, concurrency and ambient-load limitations.
Keep raw stdout/results next to the report. For timing, report repeated results
and dispersion rather than a single favorable sample.

The canonical signature scripts set one thread and an 8 MB hash and read the
current depth/counts from their source file. Run them on a fresh Release build.
A mismatch is a finding to investigate; do not call a deterministic count change
noise or overwrite the baseline to make a refactor pass.

## Match runner

Example comparing two external big networks with the same classical binary:

```bash
python tools/nnue/match.py --engine build/bin/ChessEngine --base-engine build/bin/ChessEngine --arbiter build/bin/ChessEngine-validator --net artifacts/candidate.nnue --base-net artifacts/baseline.nnue --sprt 0 5 --games 12000 --nodes 10000 --concurrency 2 --seed 2024
```

Supply files you have already validated. Windows executable paths need `.exe`;
MSVC also needs `Release/`. A runner failure is not an SPRT rejection. Preserve
W/D/L, game cap, hypotheses, LLR thresholds and the final accepted/rejected/
inconclusive status. Color-paired openings reduce one source of bias; they do
not remove every correlation or referee error.

The current runner uses this engine's validator as referee. Its
[material-adjudication defect](LIMITATIONS.md#material-adjudication) can affect
results and must be accounted for before treating a match as decisive. Independent
rule checks are valuable even when the two tested engines agree.

Use crazyhouse for drop-play experiments; a standalone bughouse game without
partner feed acquires no incoming reserves. Do not present that as a benchmark
of partner-aware bughouse strength. Native and WASM throughput need separate
measurements, with transport/rendering overhead identified.

## Reporting a change

State the concrete change, before/after configuration, measured result, and
uncertainty. An SPRT acceptance applies to its hypotheses and tested setup; a
large point estimate from a very short match is not a precise Elo estimate.
Keep historical experiments labelled by commit and net identity. If the raw
artifacts or identity cannot be recovered, report that limitation rather than
reconstructing a plausible experiment.
