## STK-Vector-64 v1.1.1

Syzygy root ranking now respects UCI `searchmoves` and passes earlier repetition
history to DTZ probing. The shipped STK-HalfKA topology, weights and standard
search fingerprints with tablebases disabled are unchanged.

Changes since v1.1.0:

- DTZ and WDL fallback rank only allowed legal root moves, including when all
  globally optimal moves are excluded by the caller.
- DTZ receives repetitions since the last capture or pawn move, including an
  earlier cycle when the current root has not repeated. A FEN alone cannot
  reconstruct game history; supply the moves in the UCI position command.
- Adapter regression tests and optional real-table tests cover restricted
  search, repetition history, fallback and the fifty-move boundary.
- Release publication finds authenticated drafts omitted by GitHub's tag
  endpoint while retaining source, checksum and upload verification.
- Corrected stale Syzygy documentation and updated the README video preview.

Known material-adjudication, network-replacement and Syzygy boundaries remain;
read `LIMITATIONS.md` in the tagged source. Matching external WDL/DTZ files are
required for tablebase coverage and are not bundled. There is no absolute Elo
or general speedup claim.

Download `release-notices.zip` with the executable. `release-source.tar.gz`
contains the corresponding source. Verify downloads with `SHA256SUMS`.
Per-platform `.build.json` files and `release-builds.json` identify the
source, toolchain, flags, embedded network and UI bundle.

Every platform ships six executables (`.exe` last on Windows):

| Suffix | Capability |
|---|---|
| *(none)* | Standard chess with classical evaluation. |
| `-nnue` | Standard chess with the shipped network embedded. |
| `-all` | Standard chess with NNUE; crazyhouse and bughouse use classical evaluation. |
| `-variants` | Drop variants with classical evaluation, no embedded net. |
| `-validator` | Legality, terminal and FEN queries as one-line JSON. |
| `-viz` | Vector Scope with the network and UI embedded. |

`x86-64-v3` needs AVX2 and BMI2; `x86-64-v2` needs SSE4.2 and POPCNT.
Windows requires AVX2. `arm64-dotprod` requires ARMv8.2 dot-product;
plain `arm64` targets ARMv8-A. Linux assets are built on Ubuntu 24.04;
compiler/runtime and macOS deployment details are in the build records.

The notices archive preserves component terms and the model card;
it does not establish missing network training provenance or grant new rights.
