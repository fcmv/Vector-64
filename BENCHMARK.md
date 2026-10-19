# Benchmarks and search evidence

Measured search and move-generation results are below, followed by reproduction
commands and evidence requirements. The expected search fingerprints live in
[tools/bench_signature.txt](tools/bench_signature.txt). No absolute Elo rating
is established by these throughput measurements. The two completed collections
below are separate runs on the same machine and build. Their individual medians
are retained rather than pooling them into a larger sample.

## Baseline collection: 2026-10-19, 11:39-11:42 IST

User-run measurements on an Intel Core i5-12450HX (8 physical cores, 12 logical
processors), Windows 11 Pro 10.0.26300. Engine source:
`85369956e82b82f1bba57b15d67a654f7ec14012`. Build: MSYS2 UCRT64 GCC 15.2.0,
Release, `-O3 -DNDEBUG -march=native`, LTO enabled, PGO off, visualization and
variants disabled, `OPT_KING_DANGER=OFF`. This is a locally tuned build, not the
downloaded MSVC release executable. The shipped H=1024 NNUE is embedded unchanged.

Each row summarizes five accepted measurements after one discarded workload
warmup. A fixed classical canary bracketed every workload. Its initial median
was 6,396,476 NPS with 1.19% calibration spread and a +/-5% tolerance. Two
attempts were rejected: a perft sample whose post-canary slowed by 8.21%, then
a retry whose pre-canary was 7.57% below baseline. Both remain in the evidence;
the third attempt passed. CPU affinity was not pinned, and the run did not
record temperature or power-mode telemetry.

| Workload | Nodes per run | Median time | Time range | Median throughput | Throughput range |
|---|---:|---:|---:|---:|---:|
| Classical search, depth 13, 1 thread, 8 MB hash | 5,935,930 | 932 ms | 922-937 ms | 6.369 MNPS | 6.335-6.438 MNPS |
| Embedded NNUE search, depth 13, 1 thread, 8 MB hash | 2,704,705 | 1,419 ms | 1,417-1,423 ms | 1.906 MNPS | 1.901-1.909 MNPS |
| Perft, six-position suite, single thread | 469,080,960 | 1,573 ms | 1,565-1,587 ms | 298 MNPS | 295-299 MNPS |
| Perft, six-position suite, parallel root tasks | 469,080,960 | 278 ms | 276-285 ms | 1,685 MNPS | 1,648-1,699 MNPS |

MNPS means million nodes per second. Search uses the built-in eight-position
suite; perft uses the separate six-position EPD suite at depth 5. Perft counts
legal continuations without alpha-beta search or neural evaluation, so its
throughput does not describe NNUE search speed. Classical and NNUE search also
visit different trees. These rows do not measure relative playing strength or
an implementation speedup over an earlier release.

Perft suite times come from each raw run's aggregate footer, not the sum of
rounded per-position values. Its printed MNPS values are truncated integers;
the table reports the median of those values. Small per-position timings have
limited precision. The parallel implementation starts one task per legal root
move and is not a fixed 12-worker search pool.

The [full summary](benchmarks/2026-10-19-i5-12450hx/summary.md) includes each
position and every acceptance/rejection decision.
[Original results](benchmarks/2026-10-19-i5-12450hx/results.json),
[raw transcripts](benchmarks/2026-10-19-i5-12450hx/) and
[provenance notes](benchmarks/2026-10-19-i5-12450hx/provenance.json) preserve
the recorded hashes, settings and measurements.

The original wrapper resolved the output directory and the `build_directory`
metadata string against PowerShell's native process directory, producing paths
under `C:\Windows\System32`. Actual executable paths, hashes and CMake reads
pointed to this repository. Original results are retained unchanged, with the
correct build-directory provenance recorded separately. The wrapper now resolves
relative output/build paths from the repository explicitly.

## Extended matrix: 13:04-13:29 IST

The second user-run collection completed all **145 measured samples** across
**28 search profiles and one perft profile**, with one accepted discarded
warmup per profile and five accepted measured repetitions. It reused the
earlier 6,396,476 NPS canary baseline and the same binaries, network and
engine source. Two initial calibration attempts were rejected against the
saved baseline before the third passed. Ten sample attempts were rejected:
four pre-canary drift failures and six post-canary drift failures.
All accepted payloads and
their canary brackets were checked against the original stdout logs.

The sweeps change one setting at a time. Unless a table says otherwise,
the anchor is depth 13, one search thread, 8 MB hash, MultiPV 1, standard
chess, embedded H=1024 NNUE for the neural binary, no external small net
or Syzygy tables, and default ordering persistence. CPU affinity, CPU
temperature and power settings were not recorded or controlled.

Values are **median (minimum-maximum)** across five accepted repetitions.
Each search time covers the complete eight-position suite, not one position.

### Fixed depths

| Depth | Classical nodes | Classical ms | Classical MNPS | NNUE nodes | NNUE ms | NNUE MNPS |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 220,154 | 33 (32-35) | 6.671 (6.290-6.880) | 134,250 | 64 (63-66) | 2.098 (2.034-2.131) |
| 10 | 1,140,187 | 186 (181-188) | 6.130 (6.065-6.299) | 481,484 | 245 (243-247) | 1.965 (1.949-1.981) |
| 12 | 3,245,397 | 508 (504-516) | 6.389 (6.290-6.439) | 1,414,396 | 738 (738-745) | 1.917 (1.899-1.917) |
| 13 | 5,935,930 | 931 (927-936) | 6.376 (6.342-6.403) | 2,704,705 | 1,422 (1,416-1,429) | 1.902 (1.893-1.910) |
| 14 | 11,325,264 | 1,745 (1,734-1,792) | 6.490 (6.320-6.531) | 4,754,623 | 2,507 (2,495-2,514) | 1.897 (1.891-1.906) |
| 16 | 30,363,261 | 4,649 (4,632-4,720) | 6.531 (6.433-6.555) | 15,035,962 | 8,007 (7,987-8,046) | 1.878 (1.869-1.883) |

The NNUE count **2,704,705 is total nodes at depth 13**, not 2.7 MNPS.
Its matrix median is 1,422 ms and 1.902 MNPS; the earlier baseline was
1,419 ms and 1.906 MNPS. These are separate repeated runs, not conflicting
units. The engine calculates `NPS = floor(nodes * 1000 / elapsed_ms)`.
Millisecond quantization has more influence on the 32-66 ms depth-8 samples.

### Search threads

| Threads | Classical nodes | Classical ms | Classical MNPS | NNUE nodes | NNUE ms | NNUE MNPS |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5,935,930 (5,935,930-5,935,930) | 931 (927-936) | 6.376 (6.342-6.403) | 2,704,705 (2,704,705-2,704,705) | 1,422 (1,416-1,429) | 1.902 (1.893-1.910) |
| 2 | 5,881,529 (5,648,865-7,349,135) | 695 (620-898) | 8.421 (8.184-9.262) | 3,155,964 (3,090,723-3,591,959) | 1,215 (1,172-1,402) | 2.598 (2.562-2.692) |
| 4 | 9,155,571 (8,146,961-9,682,191) | 489 (422-524) | 19.022 (17.278-19.306) | 4,901,402 (4,581,366-5,436,209) | 874 (795-964) | 5.639 (5.539-6.127) |
| 8 | 11,352,078 (11,123,148-12,557,829) | 450 (431-529) | 25.179 (21.460-27.075) | 6,281,118 (5,859,231-7,035,041) | 886 (762-1,013) | 7.329 (6.945-7.689) |
| 12 | 11,774,820 (11,223,444-13,591,240) | 426 (409-515) | 27.308 (26.391-28.271) | 7,383,552 (6,501,955-7,548,483) | 959 (824-1,056) | 7.714 (7.148-7.891) |

Threaded search visits different trees between repetitions. More NPS does
not imply the same improvement in time to depth. In this suite NNUE has
its lowest median time at four threads (874 ms); twelve threads report
7.714 MNPS but take 959 ms. The one-thread median is 1,422 ms. These are
suite observations on this machine, not a universal thread recommendation
or evidence of playing strength.

### Hash size

| Hash MB | Classical nodes | Classical ms | Classical MNPS | NNUE nodes | NNUE ms | NNUE MNPS |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 5,935,930 | 931 (927-936) | 6.376 (6.342-6.403) | 2,704,705 | 1,422 (1,416-1,429) | 1.902 (1.893-1.910) |
| 64 | 6,006,270 | 1,345 (1,340-1,356) | 4.466 (4.429-4.482) | 2,589,951 | 1,385 (1,379-1,390) | 1.870 (1.863-1.878) |
| 256 | 5,644,709 | 1,309 (1,307-1,330) | 4.312 (4.244-4.319) | 2,589,951 | 1,392 (1,382-1,395) | 1.861 (1.857-1.874) |

Hash size changes the search tree and memory behavior. The larger tables
were slower for classical search in this suite; NNUE elapsed time was
slightly lower at 64 MB than at 8 MB. The measurements do not isolate the
cause and do not establish the best hash size for longer searches.

### MultiPV

| MultiPV | Classical nodes | Classical ms | Classical MNPS | NNUE nodes | NNUE ms | NNUE MNPS |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5,935,930 | 931 (927-936) | 6.376 (6.342-6.403) | 2,704,705 | 1,422 (1,416-1,429) | 1.902 (1.893-1.910) |
| 3 | 19,362,016 | 2,968 (2,958-3,016) | 6.524 (6.420-6.546) | 12,573,810 | 6,643 (6,635-6,657) | 1.893 (1.889-1.895) |
| 5 | 27,602,463 | 4,208 (4,197-4,260) | 6.560 (6.479-6.577) | 19,856,733 | 10,693 (10,657-10,712) | 1.857 (1.854-1.863) |

MultiPV asks the search for more root lines. Its extra work is visible in
nodes and elapsed time even when throughput stays similar. Treat it as
analysis cost at a fixed depth, not a comparison of single-line strength.

### Perft by position

The same depth-5 correctness counts were validated for single and parallel
traversal in every accepted repetition. S1-S6 below are also P1-P6 in the
perft input. Position descriptions identify workload coverage; the FENs
and expected counts are the actual test contract.

| Position | Nodes | Single ms | Single MNPS | Parallel ms | Parallel MNPS |
|---|---:|---:|---:|---:|---:|
| P1 | 4,865,609 | 17 (17-18) | 287 (268-293) | 5 (5-5) | 942 (891-1022) |
| P2 | 193,690,690 | 620 (620-628) | 312 (308-312) | 110 (106-115) | 1762 (1688-1828) |
| P3 | 674,624 | 4 (4-4) | 156 (155-168) | 3 (2-3) | 248 (223-292) |
| P4 | 15,833,292 | 67 (66-68) | 237 (232-240) | 18 (16-21) | 899 (742-984) |
| P5 | 89,941,194 | 348 (347-356) | 258 (252-258) | 60 (59-63) | 1494 (1424-1529) |
| P6 | 164,075,551 | 507 (505-510) | 323 (321-324) | 90 (87-90) | 1833 (1821-1884) |

| Entire six-position suite | Nodes | Median ms (min-max) | Median reported MNPS (min-max) |
|---|---:|---:|---:|
| SINGLE | 469,080,960 | 1565 (1560-1582) | 299 (296-300) |
| MULTI | 469,080,960 | 287 (278-295) | 1632 (1589-1686) |

Aggregate values use each run's printed footer, computed from internal
elapsed totals before per-position display rounding. Do not obtain them by adding the
rounded per-position timings or averaging per-position MNPS. The parallel
mode creates one task per legal root move and is separate from the UCI
`Threads` sweep. Tiny 2-4 ms endgame samples are useful correctness cases
but weak isolated timing measurements.

Original [results](benchmarks/2026-10-19-i5-12450hx-matrix/results.json),
[summary](benchmarks/2026-10-19-i5-12450hx-matrix/summary.md),
[raw transcripts](benchmarks/2026-10-19-i5-12450hx-matrix/),
[provenance](benchmarks/2026-10-19-i5-12450hx-matrix/provenance.json) and
[file hashes](benchmarks/2026-10-19-i5-12450hx-matrix/sha256.json) preserve
the complete collection. These files were copied without changing the
recorded results. No engine workloads were rerun to prepare this report.

## Workload definitions

### Search position registry

The built-in `bench <depth>` command uses these eight positions in this order.
The first six also form the perft suite. The exact definitions live in
[src/uci/uci.cpp](src/uci/uci.cpp); the recorded source hash and engine commit
identify the definitions used for each historical run.

| ID | Coverage | Perft input |
|---|---|---|
| S1 | Initial position | P1 |
| S2 | Kiwipete: castling, pins and a dense legal move set | P2 |
| S3 | Rook/pawn endgame | P3 |
| S4 | Promotion, castling rights and check constraints | P4 |
| S5 | Promotion and tactical check evasions | P5 |
| S6 | Developed middlegame | P6 |
| S7 | Earlier middlegame with central tension | None |
| S8 | King/pawn endgame | None |

```text
S1  rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
S2  r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1
S3  8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1
S4  r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1
S5  rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8
S6  r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10
S7  r1bq1rk1/pp2bppp/2n2n2/2pp4/4P3/2NP1N2/PPP1BPPP/R1BQ1RK1 w - - 0 8
S8  8/8/1p1k4/p1p2p2/P1P2P2/1P1K4/8/8 w - - 0 1
```

Each matrix sample starts a fresh engine process. `bench` clears search state
once before its timer starts; the eight searches then share an evolving table
and ordering state. The timer includes FEN setup and the searches, including
thread setup inside search. Process launch, embedded-network startup, UCI option
setup and the initial search-state clear are outside that reported timer.
Consequently this measures suite search throughput, not startup latency or
independent searches with an empty table for every position.

### Perft reference depths

These are the committed expected leaf counts from
[test_data/standard.epd](test_data/standard.epd), not extra timing measurements.
The recorded suites used depth 5 for all six positions.

| Position | Depth 1 | Depth 2 | Depth 3 | Depth 4 | Depth 5 |
|---|---:|---:|---:|---:|---:|
| P1 | 20 | 400 | 8,902 | 197,281 | 4,865,609 |
| P2 | 48 | 2,039 | 97,862 | 4,085,603 | 193,690,690 |
| P3 | 14 | 191 | 2,812 | 43,238 | 674,624 |
| P4 | 6 | 264 | 9,467 | 422,333 | 15,833,292 |
| P5 | 44 | 1,486 | 62,379 | 2,103,487 | 89,941,194 |
| P6 | 46 | 2,079 | 89,890 | 3,894,594 | 164,075,551 |

The EPD also has depth-6 references for P1 (119,060,324) and P3 (11,030,083).
The `--perft <epd>` CLI caps the suite at depth 5. `--perft-one "<fen>" <depth>
<expected>` verifies an individual count; `--perft-divide "<fen>" <depth>` emits
root counts for diagnosis. Neither is a replacement for an internally timed,
repeated perft benchmark. External process timing also includes startup.

## Coverage and further experiments

The measured matrix is a bounded set of experiments. Combining every supported
value of every UCI option would obscure individual effects and produce an
unbounded testing program. The table defines representative coverage and states
where a protocol or runner still needs work. Proposed budgets below are future
experiment definitions; they are not measured results or performance claims.

| Measurement family | Cases | Current evidence or missing work |
|---|---|---|
| Legal move generation | P1-P6, perft depths 1-5, single and parallel traversal | Depth-5 timing measured above; reference counts listed for all five depths. Broader special-rule positions remain correctness coverage work. |
| Fixed-depth search | S1-S8 at depths 8, 10, 12, 13, 14, 16 | Measured for classical and embedded NNUE. Per-position search timings are not emitted by the current `bench` command. |
| Thread scaling | 1, 2, 4, 8, 12 threads at the anchor depth/hash | Measured; compare node ranges and time to depth alongside NPS. Affinity and core-class isolation remain unmeasured. |
| Hash scaling | 8, 64, 256 MB at the anchor depth/thread count | Measured. Larger budgets and longer searches require separate runs and available memory. |
| Analysis cost | MultiPV 1, 3, 5 at the anchor | Measured. PV quality and move agreement remain separate checks. |
| Fixed-node search | Proposed 10,000; 100,000; 1,000,000 nodes per S1-S8 position | UCI `go nodes` exists; the matrix runner does not collect this. Need a final-result metrics contract and a dedicated driver. |
| Fixed-time search | Proposed 100; 1,000; 5,000 ms per S1-S8 position | UCI `go movetime` exists; no recorded timing sweep. Report actual elapsed time, completed depth, move/score and stop overshoot. |
| Clock management | Proposed 10+0.1 and 60+0.6 games, paired openings | UCI clock inputs exist. Need a clock-based match harness, time-loss accounting and game evidence; the included NNUE match runner uses fixed nodes. |
| Relative strength | Candidate/base networks or engine revisions, fixed openings and budget | The included match/SPRT runner exists; these throughput runs contain no match or Elo evidence. |
| Tactical and endgame quality | Versioned EPDs with expected moves or scored outcomes, licensed/provenanced inputs | Need a published corpus, scoring protocol and per-case output. The speed suite is not a tactical accuracy test. |
| Tablebases | Absent/present tables, WDL/DTZ and rule-50 edge cases | No timing collection. Identify table files and cache state, and account for the current Syzygy integration limitations. |
| Evaluator cost | Full accumulator refresh, incremental make/unmake update, forward pass | Profiling helper exists; isolated latency/throughput and counter evidence are not recorded here. |
| Network loading | Embedded/external equivalent weights, corrupt-file handling, cold/warm startup | No performance collection. Transactional reload remains a documented correctness gap. |
| Search reset state | Fresh process, fresh game per position, persistent game/history | Only fresh process per suite measured. Other reset policies need separate labelled experiments. |
| Build/ISA | Native/portable; LTO/PGO; compiler; distributed release executable | Only the native GCC build measured. The released `.exe` has matching network identity, but its throughput is not measured here. |
| Platform/transport | Native engine, WASM worker, UI request/render path | No WASM or UI timings. Separate engine time from transport, isolation/startup and rendering. |
| Variants | Standard chess, crazyhouse, bughouse with defined reserve/partner inputs | Only standard chess measured. Variant builds need their own legal-count corpus, search positions and strength protocol. |
| Resource use | Peak RSS, resident network/table memory, energy per search, sustained-load stability | Not recorded by these collectors. Add independent measurements without silently mixing instrumentation overhead into timing results. |

### Fixed-node and fixed-time protocol

For a future per-position driver, set threads, hash, MultiPV, network and
variant explicitly; perform the UCI handshake and wait for `readyok`. Reset
with `ucinewgame` before each unrelated position, send `position fen ...`, then
one `go nodes <budget>` or `go movetime <milliseconds>` command. Wait for
`bestmove` before issuing `quit` or starting the next sample. Piping `go` and
`quit` together can interrupt the asynchronous search.

Node limits are polled and may be exceeded. In threaded search, per-search
limits and the total reported helper work also need separate interpretation.
The existing `info` output describes completed iterations; a budget can stop
partway through the next iteration. Its last `nodes` and `time` therefore must
not be presented as exact final-search totals. Record completed-iteration
metrics and external request-to-`bestmove` latency as distinct quantities until
a final-metrics interface exists. Retain full stdout, move, score, depth,
seldepth, requested budget, actual latency, options and repeat identity.

For clocked games, define opening source/hash, seed, color pairing, per-engine
threads/hash, process concurrency, adjudication and time-loss rules. Retain
PGNs and clock logs. Do not infer clock performance from fixed-node games or
infer Elo from a throughput ratio. Tablebase, terminal and mate cases can stop
early, so classify those outcomes rather than treating every short search as
a speed improvement.

### Evaluator and build comparisons

Keep the published H=1024 architecture and network fixed when comparing
implementation speed. Record the network hash and any external small-net
options; the measured runs use no external small network. An experiment with
different weights or selection thresholds is a different configuration.

[tools/profile_nnue.sh](tools/profile_nnue.sh) creates an `ENGINE_PROF` build
and collects NNUE instrumentation during a fixed-depth search. Its counters
help identify cost distribution; instrumented timings belong in a separate
report. Absolute tick values are architecture dependent. A future evaluator
microbenchmark should isolate refresh, incremental update and forward kernels,
verify outputs, and cover captures, castling, en passant, promotions, king
bucket changes and variant drops where supported. Repeated UCI `eval` commands
include command handling and position setup and do not isolate these kernels.

Compare native and portable builds, release downloads, PGO/LTO and compiler
changes with identical weights and inputs, labelled binaries and raw evidence
for every candidate. Keep a fixed canary executable across those comparisons.
The existing [tools/bench.sh](tools/bench.sh),
[tools/bench_pgo.sh](tools/bench_pgo.sh) and
[tools/bench_arm.sh](tools/bench_arm.sh) use helpers in
[tools/lib_bench.sh](tools/lib_bench.sh) that select best-of-N timings. Their
NNUE helper can automatically select a local training output; provide an
explicit `EVALFILE` when using them for reproducible experiments. Their
selection policy and reset configuration differ from this repeated-median
collection, so report them as separate experiments.

## Collect search and perft results

Earlier samples collected while the machine was hot and under load are excluded
from the recorded results above. The verified depth-13
regression fingerprints are 5,935,930 nodes for classical search and 2,704,705
nodes for the shipped NNUE. Those counts identify the search configuration;
they do not measure speed or playing strength.

On Windows, [tools/run_benchmarks.ps1](tools/run_benchmarks.ps1) collects both
search profiles and single/multi-thread perft. It uses existing binaries and
does not build or download anything. Run from the repository root when the
machine has cooled and competing CPU/GPU work has stopped:

```powershell
.\tools\run_benchmarks.ps1 -Mode All -BuildDir build-benchmark -Notes "Record power mode, background work and cooling conditions here"
```

The default is one discarded warmup and five measured repetitions per profile.
Search runs at depth 13 with one thread and an 8 MB hash, in a fresh process
for each sample. Perft uses all six positions from `test_data/standard.epd` at
the CLI's depth-5 cap, totaling 469,080,960 nodes per single/multi traversal.
Multi perft launches one task per legal root move; it is not a fixed-size search
worker pool. The engine prints perft seconds to three decimals and truncates
reported MNPS to an integer. Short-position timing precision is limited.

To collect the two workloads separately:

```powershell
.\tools\run_benchmarks.ps1 -Mode Search -BuildDir build-benchmark
.\tools\run_benchmarks.ps1 -Mode Perft -BuildDir build-benchmark
```

Override `-Classical` and `-Nnue` to use other binaries, or add
`-ReleasedNnue <path-to-released-nnue.exe>` for a separately labelled release
comparison. Supply the build directory matching those binaries to record its
CMake settings; external release toolchain identity must be recorded separately.
Use `-Repeats`, `-Warmups`, `-TimeoutSeconds` and `-Output` to change collection
settings. New runs require an unused output directory; interrupted runs can
resume in their original directory with matching settings.

### Fixed-depth matrix runner

Use `-Matrix` to collect multiple fixed depths and sweep thread count, hash size
and MultiPV. It uses the same drift guards, logs, retries, checkpoints and archive
as the canonical runner. The default focused sweep changes one setting at a time
from depth 13, one thread, 8 MB hash and MultiPV 1. It always includes that anchor.
Depths default to 8, 10, 12, 13, 14 and 16; hashes to 8, 64 and 256 MB; MultiPV to
1, 3 and 5. Default thread counts are 1, 2, 4, 8, 12, 16, 32 and 64, filtered to
the machine's logical processor count.

Preview first. `-Plan` reads configuration and hashes without launching engines
or creating a benchmark output directory:

```powershell
$benchmarkRun = @{
    Matrix = $true
    Mode = 'All'
    BuildDir = 'build-benchmark'
    Output = 'artifacts/benchmarks/depth-matrix'
    Depths = @(8, 10, 12, 13, 14, 16)
    ThreadCounts = @(1, 2, 4, 8, 12)
    HashSizes = @(8, 64, 256)
    MultiPV = @(1, 3, 5)
    Repeats = 5
    Warmups = 1
    Notes = 'Record power mode, cooling and background work here'
}
.\tools\run_benchmarks.ps1 @benchmarkRun -Plan
.\tools\run_benchmarks.ps1 @benchmarkRun
```

On the recorded 12-logical-processor machine, this focused plan has 28 search
profiles and one single/multi perft profile, with 145 measured samples and 29
discarded warmup samples. Every candidate is bracketed by the fixed classical
canary. Larger depths and MultiPV settings can take substantially longer; the
default process timeout is 300 seconds. Override `-TimeoutSeconds` before
starting if needed, and retain the same settings on resume.

After an interruption or drift pause, cool/idle the machine and use the same
hashtable, output directory and settings:

```powershell
.\tools\run_benchmarks.ps1 @benchmarkRun -Resume
```

Share `artifacts/benchmarks/depth-matrix.zip`. Completed samples are retained on
resume; a completed run exports its results without repeating workloads. For a
new experiment, choose a new output directory. The lower-level entry point is
[tools/benchmark_matrix.py](tools/benchmark_matrix.py); use `--help` for controls.

`-Sweep Full` explicitly requests the Cartesian product of the supplied axes.
With the values above, that is 540 search profiles plus perft, or 2,705 measured
samples before warmups and canaries. Use `-Plan` to inspect it before running.
The focused sweep is the default because it makes individual effects easier
to interpret and keeps the workload bounded.

Each search candidate uses the built-in eight-position suite in a fresh process.
The engine clears search state once at suite start, then carries the evolving
state between positions. The runner verifies each binary's canonical depth-13
fingerprint before calibration. Only the depth-13, one-thread, 8 MB, MultiPV-1
profile has a committed golden node count. Other single-thread profiles require
repeatable node counts; this is a consistency check, not independent correctness
proof. Threaded search can visit different numbers of nodes, so the matrix
summary reports node ranges alongside time and NPS ranges. An option rejection,
wrong canonical fingerprint or changed single-thread count stops collection.

The matrix covers fixed-depth search and depth-5 perft. Fixed-node searches,
fixed-time searches, game matches, isolated evaluator microbenchmarks, tablebase
and variant workloads require separate protocols and are not collected by this
script. Search throughput does not establish Elo or strength scaling.

### Canary and machine drift

The collector uses a fixed engine as a canary. By default this is the classical
binary, at the same depth-13, one-thread, 8 MB hash configuration. Override it
with `-Canary <reference.exe>` and use `-CanaryNodes <count>` if its expected
fingerprint differs from the current classical signature. Keep that reference
binary unchanged when comparing candidates.

The sequence is:

1. Run a discarded canary warmup and three calibration samples. Reject
   calibration when `(maximum NPS - minimum NPS) / median NPS` exceeds 5%.
2. Establish the median as the baseline, or check against a supplied previous
   baseline. Resume always retains the saved baseline.
3. Bracket every warmup and measured workload with canary runs. Both must stay
   within +/-5% of baseline, and the after/before canary ratio must also stay
   within that tolerance. Check speedups as well as slowdowns; otherwise an
   initially loaded machine becoming idle could bias the comparison.
4. Skip the workload after a failed pre-check. Reject an already-run workload
   after a failed post-check. Keep every failed/rejected attempt and its logs.
   Do not rescale its timing or include it in the accepted median.
5. Retry at most twice after the first attempt, with a ten-second cooldown.
   Pause after exhaustion, preserving accepted samples. Process timeouts and
   nonzero exits are also bounded retries; wrong fingerprints or malformed
   result data stop immediately. Each sample normally has a one-second idle
   pause before it. These defaults are configurable.

The guard measures workload throughput, not temperature. It cannot identify an
initially slow but stable machine without a known-good reference. A single-thread
canary can also miss interference affecting only multicore perft, NNUE-specific
resources, or a brief interval inside the measured workload. It is a quality
gate, not proof of isolated hardware conditions. Record power/cooling/background
conditions and inspect rejected attempts alongside the medians.

The defaults are explicit in a typical run:

```powershell
.\tools\run_benchmarks.ps1 -Mode All -Output artifacts/benchmarks/cool-run -DriftPercent 5 -CanarySamples 3 -CooldownSeconds 1 -RetryDelaySeconds 10 -Retries 2
```

After cooling the machine or removing competing work, resume with the same
mode, paths, sample counts and controls:

```powershell
.\tools\run_benchmarks.ps1 -Mode All -Output artifacts/benchmarks/cool-run -Resume
```

The example resume uses the default controls from the preceding command.
Non-default controls must be repeated. Completed accepted samples are skipped;
calibration and warmups run again against the original baseline. The resume
identity includes source/collector revisions, machine, binary/network/input
hashes and numerical controls. Changes require a fresh output directory.

For a new run checked against a previously recorded cool-machine baseline:

```powershell
.\tools\run_benchmarks.ps1 -Mode All -Output artifacts/benchmarks/comparison -CanaryReference artifacts/benchmarks/cool-run/results.json
```

The reference must have a valid baseline and match the machine, canary binary,
benchmark workload and canary settings. It may also be a previous `partial.json`
with established calibration. On resume omit `-CanaryReference`; the saved
checkpoint already contains that baseline. Workload order rotates between
repetitions to reduce fixed-order bias.

Each successful run writes `results.json`, a readable `summary.md`, and raw
warmup/measured transcripts under `artifacts/benchmarks/<timestamp>/`, then
creates a sibling ZIP to share. Machine metadata and executable/network hashes
are included. A failed/interrupted run keeps `partial.json` and completed logs;
it must not be reported as a completed benchmark. Checkpoints use a flushed
temporary file and atomic replacement. An OS file lock prevents two collectors
from writing the same run. Ctrl+C and per-process timeouts terminate the active
engine process. A hard power loss or forced termination of the parent is outside
that cleanup guarantee. No CPU affinity or power/thermal settings are changed.
The wrapper packages checkpoints/logs after a normal paused/failed exit as well
as completion. `summary.md` includes all acceptance/rejection decisions and drift
percentages; `results.json` is produced only once every planned sample is accepted.

The underlying [Python collector](tools/benchmark.py) uses only the standard
library and can also run on other platforms with their executable paths:

```bash
python tools/benchmark.py --mode all --engine classical=build/bin/ChessEngine --engine nnue=build/bin/ChessEngine-nnue --perft-engine build/bin/ChessEngine --canary build/bin/ChessEngine --output artifacts/benchmarks/manual-run
```

Source changes under `src/`, `app/`, `tests/cpp/` or `CMakeLists.txt` must be
committed before collection so the recorded source revision is identifiable.
Build the desired binaries before cooling the machine; the collector records
their hashes but cannot prove that an arbitrary executable matches the checkout.

The collection approach follows the warmup, cooldown, repeated-median and
correctness-first practices in [Lucen's matrix benchmark](https://github.com/fcmv/lucen/blob/dcc365eee3bf01d069bfce83d101bc0246f5a869/tests/benchmarks/matrix_bench.py).
The machine-drift brackets and recoverable run state are additions here; the
inspected Lucen drivers did not contain that canary protocol. Synthetic failure
and drift tests are in `tests/python/test_benchmark.py`; they do not run chess
performance workloads.

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
