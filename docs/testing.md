# Testing

Run from the repository root on a fresh Release build. Commands use the default
single-configuration `build/bin/` layout; MSVC uses `build/bin/Release/*.exe` and
requires `ctest -C Release`. Test counts depend on enabled targets and changes;
list them with `ctest --test-dir build -N` rather than relying on a copied count.

## C++ correctness

```bash
ctest --test-dir build --output-on-failure
```

Perft checks known legal trees. State tests rebuild incremental fields and verify
undo. NNUE tests compare integer scalar/SIMD and incremental/full paths. Variant
tests add reserves, promoted markers and drops. Visualization tests capture
inference, replay session moves, and exercise dataset shards and wire fixtures.
These are separate properties; none alone proves complete rule adjudication.

On Windows, if CTest finds the system WSL launcher instead of Git Bash, set the
intended shell at configure time:

```powershell
cmake -S . -B build-ucrt -DBASH_EXECUTABLE="C:/Program Files/Git/bin/bash.exe"
```

A failed or Not Run test is not a successful suite. Fix the environment or state
which check remains unverified; do not exclude it just to report a green run.

## Perft and divide

```bash
./build/bin/ChessEngine --perft
./build/bin/ChessEngine --perft test_data/standard.epd
./build/bin/ChessEngine --perft-one "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" 3 8902
./build/bin/ChessEngine --perft-divide "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" 3
```

The EPD suite exits nonzero on mismatch/failure. Divide prints UCI root moves and
counts followed by `Total: 8902` for this example. Depth zero is `Total: 1`;
invalid FEN/depth returns 2. `--perft-divide` belongs to the development checkout,
not the original v1.0.0 CLI. Old `--nnue-consistency` instructions are obsolete;
use CTest's consistency checks.

## Search fingerprints

```bash
bash tools/bench_signature.sh build/bin/ChessEngine
bash tools/bench_signature.sh build/bin/ChessEngine-nnue nnue
```

Expected depth/counts come from `tools/bench_signature.txt`. Both checks use one
thread and an 8 MB hash. For an intentional change only, regenerate with both
binaries using `tools/update_bench_signature.sh`; never edit counts by hand.
A fingerprint is search identity, not throughput or Elo. See
[benchmark methodology](benchmark.md).

## Python tooling and training

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check tools tests examples
python -m mypy tools tests/python tests/docs examples
ENGINE_BIN="$PWD/build/bin/ChessEngine" python -m pytest
```

The full Python suite also needs NumPy and, for training/export tests, PyTorch;
see [training setup](nnue-training.md). `ENGINE_BIN` selects the classical binary
for UCI and parity tests. In PowerShell set
`$env:ENGINE_BIN=(Resolve-Path build-ucrt/bin/ChessEngine.exe).Path` first.
Missing PyTorch or engine paths can skip checks; inspect the summary rather than
claiming the entire contract was tested.

The docs conformance suite additionally needs the validator:

```bash
ENGINE_BIN="$PWD/build/bin/ChessEngine" VALIDATOR_BIN="$PWD/build/bin/ChessEngine-validator" python -m pytest tests/docs -v
```

It checks executable examples, documented UCI option names, structured request
results/state, the feature example, and the shipped model identity. It checks
selected examples, not every English sentence or every external link.

## Visualization and UI

```bash
bash tools/viz_smoke.sh build/bin/ChessEngine-viz build/bin/ChessEngine-nnue
./build/bin/test_viz fixture "$PWD/artifacts/viz-frame.bin"
cd ui
npm ci
npm run typecheck
VIZ_FIXTURE="$PWD/../artifacts/viz-frame.bin" npm test
npm run build
```

Create `artifacts/` before writing a fixture if it does not exist. Use an
absolute `VIZ_FIXTURE` path in your shell. UI tests require the C++ fixture for
the cross-language wire contract. Rebuild/commit `ui/dist/index.html` after UI
changes; CI compares the bundle against its source build using Node 24.

The WASM job currently builds and checks the deployable file set; it does not
prove browser startup or runtime integer parity. State those checks separately.

## Sanitizers and documentation

The Unix sanitizer recipe follows CI:

```bash
cmake -S . -B build-sanitize -DCMAKE_BUILD_TYPE=Debug -DENGINE_LTO=OFF -DENGINE_NATIVE=OFF -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -g"
cmake --build build-sanitize -j
./build-sanitize/bin/test_zobrist
```

This does not establish race freedom for the shared SMP TT. Record supported
hardware when verifying ARM/AVX2-specific kernels.

```bash
python -m pip install -r requirements-docs.txt
python -m mkdocs build --strict
```

The docs workflow builds without publishing, runs conformance tests against its
own engine build, and exercises the tiny CPU training walkthrough. A generated
site is a local artifact until explicitly deployed.
