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
