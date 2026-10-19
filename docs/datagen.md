# Generate self-play training data

Generation plays games and labels positions; preparation converts those rows
into checked STK-HalfKA shards; training consumes the shards. These stages have
different output and resume contracts. This guide keeps the shipped architecture
fixed. Generating more rows alone is not evidence of a stronger network.

## Choose the generator

| Path | Parallelism and output | Resume boundary |
|---|---|---|
| `ChessEngine datagen` | Independent games; `--threads`/`--concurrency` means game workers, each with one search thread. Plain file or text shards. | No direct resume switch; a fresh run truncates its starting output. |
| `tools/nnue/datagen_bulk.py` | Runs native game chunks, stores each completed chunk and its hash. | Reuses verified completed chunks with identical settings; an unregistered partial chunk stops resume. |
| Vector Scope datagen | A visible session, text shards and a state sidecar. | Restores saved row-shaping settings and completed-game counters, appends to existing output. |

Use an explicit network path for native datagen even with `ChessEngine-nnue`:
datagen branches before the executable's embedded-network UCI setup. Without
`--net`, the generator warns and uses classical evaluation. Each worker owns
its search/hash state, so memory grows with worker count. A seed fixes opening
choices; parallel write order and timed/SMP searches are separate concerns.

## Small native run

Use an unused output directory. The following is an example for the reader to
run, not a recorded training or throughput result:

```bash
mkdir -p runs/datagen-demo
./build/bin/ChessEngine datagen --net nets/stk-vector-64.nnue \
  --out runs/datagen-demo/shards --games 4 --threads 1 \
  --nodes 1000 --depth 5 --skip-plies 4 --max-plies 80 \
  --opening-plies 8 --balance 150 --seed 2024 \
  --emit raw --shard-positions 1000 --log-interval 5
```

On PowerShell create the parent with `New-Item -ItemType Directory -Force`, use
`build/bin/ChessEngine.exe` (MSYS2) or `build/bin/Release/ChessEngine.exe` (MSVC),
and put arguments on one line or use PowerShell continuation syntax.

The output directory contains `shard_0000.txt`, then later numbered files as
needed. Rollover can leave an empty final shard. With `--shard-positions 0`,
`--out` names one file; its parent must already exist. Do not restart a raw CLI
run over a valuable dataset expecting append/resume behavior.

| Native option | Default | Meaning |
|---|---:|---|
| `--net` | none | External big network; otherwise classical eval. |
| `--out` | required | File, or directory when sharding is enabled. |
| `--games` | 20000 | Game-work allocation; failed opening attempts can skip games. |
| `--threads`, `--concurrency` | 8 | Independent game workers. |
| `--hash` | 16 | MB per worker. |
| `--nodes`, `--depth` | 5000, 9 | Per-move search limits; either can stop search. |
| `--max-plies`, `--skip-plies` | 200, 12 | Game cap and initial played plies excluded from labels. |
| `--opening-plies`, `--balance` | 8, 150 | Random opening length and material-balance bound in cp. |
| `--seed` | 0 | Base seed for per-game openings. |
| `--emit` | raw | `raw` stores eval and game result; `blend` stores blended cp. |
| `--lam` | 0.5 | Weight given to WDL when writing blended labels. |
| `--shard-positions` | 0 | Rows per shard; zero selects one file. |
| `--log-interval` | 30 | Progress heartbeat seconds. |

Use positive bounded limits. The native parser is not a complete validation
front end for arbitrary hostile numeric input. A supplied net path should be
prevalidated; the current native generator does not make every load/write
failure a strong process-level error. Inspect stderr and output rather than
counting process exit alone as a dataset-quality gate.

## Labels and termination

Native search scores are converted to **White-relative cp** before storage.
Rows skip positions in check and the configured opening portion. Scores are
clamped by the generator; complete games attach White WDL of 1, 0.5 or 0.
Repetition, the fifty-move counter, the generator's material heuristic and the
maximum-ply cap can end a game as a draw. Those policies are not a complete
tournament adjudicator. CLI and UI share row-writing helpers, but the UI can
use opening variety and different stopping policies, so they are distinct
experiments rather than guaranteed identical game streams.

Raw rows have `<fen> | <white_cp> | <white_wdl>`. Blended rows have
`<fen> | <white_cp>`. See the [data contract](spec/datasets.md) before mixing
sources: applying WDL blending a second time changes the targets.

## Bulk chunks and interruption

```bash
python tools/nnue/datagen_bulk.py --engine build/bin/ChessEngine \
  --net nets/stk-vector-64.nnue --out-dir runs/bulk-demo \
  --target-positions 1000 --chunk-games 4 --concurrency 1 \
  --nodes 1000 --emit raw --seed-base 2024
```

Repeat the identical command to resume. The target is checked between complete
chunks and can be exceeded. The wrapper records the engine path, network hash, settings,
completed chunk counts and SHA256 values in `bulk_state.json`; logs go to
`datagen_bulk.log`. It does not hash the engine executable; preserve its binary
hash/source revision yourself and keep it unchanged across resume. It refuses changed settings, altered completed chunks and
unregistered output chunks. After a crash within a chunk, preserve that partial
file separately and inspect it before choosing a fresh directory or explicitly
recovering the failed chunk. Do not edit the state to declare unfinished data
complete. Run only one writer per output directory.

## Generate in Vector Scope

Open **datagen** and choose an unused output path, target positions/game cap,
nodes/depth, label mode, shard size and seed. The API's defaults are reported
in `datagenDefaults`; typical defaults are 5000 nodes, depth 9 and five million
positions per shard. Set small targets for a first check rather than accepting
the large default target.

Start switches the session into datagen and locks controls that could change
the collected rows. Pause/stop remain available. Use **probe/resume** to inspect
an existing dataset; saved row-shaping settings take precedence on resume,
while requested position/game targets can extend the run. Completed games are
the checkpoint boundary, so a target can be exceeded by one game's rows.

The state sidecar stores counters/settings, not complete engine/RNG/TT state
or a cryptographically verified dataset manifest. Writes are not a durable
atomic transaction across every shard and state file. After power loss, audit
rows and counters and retain a backup. Do not promise bit-identical continuation
or use the sidecar as proof of input integrity. See the
[control reference](spec/telemetry.md#datagen-controls).

## Convert and validate

```bash
python tools/nnue/build_stk_data.py --input runs/datagen-demo/shards \
  --out-dir runs/datagen-demo/prepared --shard-size 1000 --dedup-scope global
python tools/smoke_test.py --data runs/datagen-demo/prepared \
  --engine build/bin/ChessEngine --device cpu
```

Keep native raw labels at the preparation default `--cp-source white`. Record
the WDL blend, filters and source identities with the run. Inspect the manifest's
kept/rejected counts and label statistics before following the
[training walkthrough](nnue-training.md). Reserve independent games/sources for
validation: row encoding and export parity do not establish label quality or
prevent leakage. Retain source rights/provenance alongside hashes.
