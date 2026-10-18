# Contributing

Start with a clean build and a reproducible change. Correct rules/state,
integer inference parity, and explicit evidence for search changes are the
project's review boundaries. The current NNUE architecture is STK-HalfKA as
specified in [the network contract](docs/vector64-spec.md).

## Set up

Follow [building](docs/building.md) for your compiler, then run:

```bash
ctest --test-dir build --output-on-failure
bash tools/bench_signature.sh build/bin/ChessEngine
bash tools/bench_signature.sh build/bin/ChessEngine-nnue nnue
```

On MSVC use `ctest --test-dir build -C Release --output-on-failure` and executable
paths under `build/bin/Release/`. Use Git Bash/MSYS2 for Bash scripts on Windows.
Install Python developer tools with `python -m pip install -r requirements-dev.txt`.
Training tests also need the [runtime dependencies](docs/nnue-training.md).

The [architecture map](docs/architecture.md) gives boundaries; the
[engineering guide](docs/implementation/engineering.md) identifies code and
invariant checks. Public setup must not depend on a private `HOUSE_RULES.md`.
That ignored file is a maintainer's local working agreement, not a clone artifact.

## Verification by change type

| Change | Evidence to include |
|---|---|
| Rules, movegen or position state | A minimal FEN/history, expected legal moves/counts from an independent source where possible, make/unmake/hash checks, and full CTest. |
| Search/order/pruning | Both fingerprints; explain intended count changes. Supply controlled match evidence for a playing-strength claim. |
| Integer kernels/accumulators | Scalar/SIMD and incremental/full comparisons on affected supported architectures, including special-move cases. |
| Network weights/data/export | Data/model identity, encoding/perspective, layout and integer engine parity, plus separate quality/strength evidence. |
| Python tools | Ruff, mypy and the relevant/full Python suite with needed binaries supplied. |
| Visualizer/UI/wire | Telemetry/session tests and smoke test; C++ fixture/TypeScript decoder contract; rebuild committed HTML after UI changes. |
| Documentation/examples | Strict site build, links, executable examples, and protocol-option checks against the documented binaries. |

A failed or skipped applicable check is not a pass. State what was run and which
parts remain unverified. Tests must distinguish behavior from implementation,
especially where engine paths share a potentially wrong rule predicate.

## Search fingerprints and strength

`tools/bench_signature.txt` is the single expected-count source. A refactor or
isolated variant change intended to preserve standard search should keep both
counts. If a deliberate search or shipped-net change moves them, regenerate
with the script and include that change with the implementation:

```bash
bash tools/update_bench_signature.sh build/bin/ChessEngine build/bin/ChessEngine-nnue
```

Do not hand-edit counts. A higher NPS is not a strength result; a short match
with an inconclusive SPRT is not an accepted improvement. See
[BENCHMARK.md](BENCHMARK.md) for required run metadata and interpretation.

## Code and review

Keep changes focused and match the surrounding style. Comments should explain
non-obvious constraints, not narrate code. Preserve the standard/variant compile
boundary, mover-relative NNUE output, independent visualization dependencies,
and native/WASM source-list consistency.

Describe the problem, resulting behavior, verification, and material limitations
in a PR. Keep commit subjects short, one line, ASCII, without tooling-attribution
trailers. A reviewer should be able to reproduce the evidence without access to
personal datasets or untracked historical binaries. Record unknown provenance
as unknown rather than filling in plausible history.

Use the root [Apache license](LICENSE) for the engine contribution context and
read [component notices](THIRD_PARTY_NOTICES.md) for UI/vendor boundaries. Preserve
upstream license texts and attributions. This documentation does not relicense
third-party components or establish new rights over externally sourced weights.

## Documentation workflow

```bash
python -m pip install -r requirements-docs.txt
python tools/docs/check_punctuation.py
python -m mkdocs serve
python -m mkdocs build --strict
```

Root policy/reference documents are canonical; `docs/` site pages include them.
Changing a rule or option should update its owning reference and its executable
fixture in the same change. Keep future feature decisions outside current-behavior
reference pages. Support/reporting routes are in [SUPPORT.md](SUPPORT.md).

Use ASCII punctuation instead of em or en dashes in documentation. The docs
workflow checks the repository's Markdown, reStructuredText and AsciiDoc files.
