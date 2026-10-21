## STK-Vector-64 v1.1.0

Vector Scope, shared NNUE training tools and release provenance join fixes for
threaded search, deferred NNUE accumulators, datagen recovery and append-safe
recording. The shipped STK-HalfKA topology and weights are unchanged.

Highlights since v1.0.0:

- Coherent transposition-table snapshots and consistent classical evaluation
  in drop-variant helper threads.
- Deferred big-network accumulator updates when optional evaluation gates skip
  the big network; shared search/depth limits and explicit browser worker stacks.
- Validated HTTP/WASM dataset recovery, append-preserving recordings and
  deterministic, integrity-checked RL input preparation.
- Shared training/export/parity tools, perft divide, guarded benchmark matrix,
  refreshed Vector Scope UI and current architecture/protocol documentation.
- Six-platform release checks with exact-commit CI gates and verified assets.

Known material-adjudication, network-replacement and Syzygy boundaries remain;
read `LIMITATIONS.md` in the tagged source. Browser recovery does not add durable
storage across reloads. There is no absolute Elo or general speedup claim.

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
