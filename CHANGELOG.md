# Changelog

User-visible changes are grouped by release. Unreleased entries describe source
on `main`; they are not capabilities promised for an older downloadable binary.
The NNUE feature set and topology remain fixed to the published v1.0.0 Windows
NNUE executable. See [version selection](docs/versions.md).

## Unreleased

No changes recorded yet.

## v1.1.1 - 2026-10-24

### Fixed

- Syzygy root ranking respects UCI `searchmoves`, including when the allowed
  set excludes every globally optimal move. DTZ and WDL fallback rank only
  the caller's legal candidates.
- DTZ receives repetition history since the last capture or pawn move,
  including earlier cycles when the current root has not repeated.
- Draft release lookup uses the authenticated release list when GitHub's
  tag endpoint omits drafts, allowing verified uploads to resume normally.
- Stale Syzygy documentation now describes the existing variant guards,
  root restrictions, repetition handling and optional real-file verification.

### Added

- Adapter regressions for restricted ranking, tied moves, underpromotions,
  repetition propagation and missing-table fallback. Optional external-file
  tests cover real DTZ/WDL probing, the fifty-move boundary and threaded search.
- The README preview opens the final video with the platform and repository card.

The shipped NNUE topology and weights are unchanged, as are both standard
search fingerprints with tablebases disabled. Material adjudication and failed
network-replacement limitations remain; see [LIMITATIONS.md](LIMITATIONS.md).
No absolute Elo or general performance improvement is claimed.

## v1.1.0 - 2026-10-21

### Added

- Release checks for all six platform capabilities, exact-commit CI gates,
  corresponding source and dependency notices, build identity and SHA256 manifests.
- A `CI complete` gate, workflow linting, full Python/CTest coverage and pinned
  Emscripten validation; applicable skipped Python checks fail CI.
- Community governance, conduct, issue forms and review ownership, with triage
  guidance and disabled protection/label templates for maintainer review.
- Draft-first release uploads with server-side hash verification and refusal
  to replace public assets; immutable action pins and merge-group CI support.
- `--perft-divide "<fen>" <depth>` for legal root-move counts and diagnostics.
- A shared STK-HalfKA preparation, training, quantization, export and integer
  verification pipeline, with a small runnable CPU example.
- Resumable benchmark collection with bounded retries, fixed canary drift
  checks, raw transcripts and a fixed-depth/thread/hash/MultiPV matrix.
- Identified classical/NNUE search and perft measurements on the i5-12450HX,
  with the original evidence preserved in `benchmarks/`.
- Documentation for current protocols, architecture, limits, contribution and
  release procedures; executable documentation checks and a strict docs build.

### Changed

- Big-network accumulator updates can be deferred when small-network or lazy
  evaluation skips the big network. The shipped weights and topology are unchanged.
- Shared perft diagnostics now live in `src/perft/`, vendored Fathom in
  `third_party/fathom/`, and build definitions in focused `cmake/` modules.
  Presets place new builds under `out/build/`; `BUILD_TESTING=OFF` omits tests.
- Benchmark and experiment implementations are grouped under `tools/bench/`
  and `tools/experiments/`. Python tools use package imports while existing
  file commands and launchers remain supported.
- Training entry points share feature, label-perspective, dataset and export
  contracts. Legacy switches and incompatible HalfKP data are rejected; see
  [training migration](docs/nnue-training.md#migration).
- Browser startup reports initialization/isolation failures and offers recovery.
- Vector Scope uses true-black backgrounds, clearer panel borders, a neutral
  board and silver controls. Neural activations and contribution traces retain
  vivid colors and stronger inspection highlights.
- Maintainer-local `CLAUDE.md` and `HOUSE_RULES.md` are no longer tracked.

### Fixed

- Drop-variant search workers consistently suppress standard NNUE evaluation
  and updates, including when a standard network is loaded.
- Transposition-table stores and probes use coherent synchronized snapshots
  in threaded search; sampled node and tablebase counters publish atomically.
- Search, UCI and visualizer share depth limits. Browser builds reserve 8 MiB
  stacks for main and worker threads and enable stack overflow checks.
- Datagen recovery validates HTTP/WASM replies, reports failures and prevents
  a stale output-path probe from authorizing a different destination.
- Recording appends preserve existing bytes and separate an unterminated last
  record. RL input preparation validates deterministic inputs and source manifests.
- Benchmark provenance checks include staged and untracked source inputs.
- Unused helpers and stale implementation comments were removed or corrected.
- `ENGINE_VIZ=OFF` configures without creating visualization targets or tests.
- Relative benchmark build/output paths resolve from the repository, including
  when PowerShell's native process directory differs from its shell location.
- Training/parity and match tooling distinguish identity failures, failed
  workers and inconclusive strength tests from successful results.

Known material-adjudication, network-reload and Syzygy boundaries remain in
[LIMITATIONS.md](LIMITATIONS.md). This history does not mark them repaired.

## v1.0.0 - 2026-09-24

Source commit: `b301d4fea0faf08fa2cf774438b532b027503fd7`.

The tagged release distributes classical, embedded-NNUE, combined variant,
variant-only, validator and Vector Scope executables across its published
platform profiles. The shipped H=1024 network uses the existing STK-HalfKA
contract. Assets are bare executables, with no complete checksum/notice bundle.

Use the [verified v1.0.0 guide](docs/releases/v1.0.0.md) and
[release assets](https://github.com/fcmv/Vector-64/releases/tag/v1.0.0).
This entry summarizes identifiable release scope rather than reconstructing
unrecorded experiments or assigning an Elo rating.

[Compare v1.0.0 with main](https://github.com/fcmv/Vector-64/compare/v1.0.0...main).
