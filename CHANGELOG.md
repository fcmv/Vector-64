# Changelog

User-visible changes are grouped by release. Unreleased entries describe source
on `main`; they are not capabilities promised for an older downloadable binary.
The NNUE feature set and topology remain fixed to the published v1.0.0 Windows
NNUE executable. See [version selection](docs/versions.md).

## Unreleased

### Added

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

- Training entry points share feature, label-perspective, dataset and export
  contracts. Legacy switches and incompatible HalfKP data are rejected; see
  [training migration](docs/nnue-training.md#migration).
- Browser startup reports initialization/isolation failures and offers recovery.
- Vector Scope uses true-black backgrounds, clearer panel borders, a neutral
  board and silver controls. Neural activations and contribution traces retain
  vivid colors and stronger inspection highlights.
- Maintainer-local `CLAUDE.md` and `HOUSE_RULES.md` are no longer tracked.

### Fixed

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
