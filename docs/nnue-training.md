# STK-HalfKA training

All PyTorch entry points use `tools/nnue/make_net.py`, `STKNet` and
`halfka_features.py`. The model has 22528 features per perspective, 1024 or
128 accumulator neurons, pairwise activations, eight output buckets and a
PSQT side output. Model outputs are side-to-move relative. The stored dataset
labels are white-relative; training flips black-to-move labels exactly once.

The architecture is fixed to the published Windows v1.0.0 `-nnue.exe`, recorded
in the [STK-HalfKA contract](vector64-spec.md).
This guide changes no layer sizes or feature scheme. Commands assume the
repository root and a classical, non-embedded engine for parity.

## Install dependencies

Python 3.10+ is the tooling language target; the CPU training CI uses Python 3.11.
Use a virtual environment. CPU-only installation avoids the CUDA-index default
in `requirements.txt`:

```bash
python -m pip install "torch>=2.2,<2.6" --index-url https://download.pytorch.org/whl/cpu
python -m pip install "numpy>=1.23,<3" "tqdm>=4.70.1,<5" "zstandard>=0.22,<0.24" "datasets>=2.19,<3"
```

For the configured CUDA 12.1 wheel path use
`python -m pip install -r requirements.txt`. CUDA wheel availability depends on
Python/platform. A PyTorch wheel alone is not the full CUDA toolkit needed by
Bullet. Training is FP32 in the shared supervised path.

Run `python tools/check_gpu.py` to inspect CUDA availability and time a warmed,
synchronized matrix multiplication. This diagnostic does not measure training
throughput or require CUDA for CPU training.

The RL loop writes a generation-local sampling manifest (`train_input.json`)
beside its immutable `train_input.txt`. Restarting validates input/source hashes
and sampling settings; it does not overwrite an interrupted trainer's input.
Sampling uses a generation-local seed, so publication interrupted before the
input rename can be reconstructed. Legacy input without a manifest is preserved
and rejected for automatic reuse; retain that run and validate its provenance
before migration, or start a separate workdir. These guarantees concern input
preparation, not identical GPU training or stochastic match outcomes.

## Tiny CPU walkthrough

Build `ChessEngine` first. The committed `examples/training_positions.txt` is a
synthetic eight-position demonstration, not training evidence for a strong net.
Use a new workdir for a fresh run:

```bash
python tools/run_pipeline.py --input examples/training_positions.txt --workdir runs/docs-cpu --hidden 128 --epochs 1 --batch-size 4 --shard-size 4 --device cpu --engine build/bin/ChessEngine --tolerance-cp 0 --output artifacts/docs-candidate.nnue
python tools/nnue/check_vector64.py artifacts/docs-candidate.nnue
```

For MSVC use `build/bin/Release/ChessEngine.exe`; for MSYS2 use
`build/bin/ChessEngine.exe`. This small-network run needs much less memory than
the big trainer and exercises the same contract. It writes checked data shards,
resume state, float weights and an exported net, then compares integer engine
inference and color mirrors. The checker should report H=128 and 6,510,649 bytes.
Do not replace the shipped net with this demonstration.

## Preparation and preflight

Install the CPU or CUDA dependencies described above and build the classical
`ChessEngine` and `ChessEngine-validator` targets. CPU works for
small tests; CUDA is useful for full training. MSVC paths include
`build/bin/Release/`; MSYS2 paths use `build/bin/`. Windows names end in `.exe`.

```bash
python tools/smoke_test.py --engine build/bin/ChessEngine --device cpu
python tools/nnue/build_stk_data.py --input positions.jsonl.zst \
  --out-dir runs/candidate/data --shard-size 1000000 --dedup-scope global
python tools/smoke_test.py --data runs/candidate/data \
  --engine build/bin/ChessEngine --device cpu
```

Input accepts Lichess eval JSONL, zstd JSONL, `<fen> | <cp>` text, directories
of text shards, or `hf://DATASET_ID` (requires `datasets`). For Lichess records,
`--min-depth` and `--min-knodes` choose the deepest qualifying evaluation.
Mate scores map to +/-8000 cp and are excluded by the default 6000 cp filter.
Bullet text `<fen> | <eval> | <wdl>` is blended with `--wdl-lambda` in win
probability space. Numeric labels must be finite. Use `--cp-source stm` only
for input labels already relative to the mover.

Deduplication supports `none`, `shard` and disk-backed `global` scopes. The key
includes board, mover, castling rights and en passant; clocks do not affect it.
Preparation records source file identity and settings and writes progress at
completed shard boundaries. Interrupted partial shards are replayed. Changing
source files or preparation settings requires a new output directory.

NPZ arrays are `white_indices`, `black_indices` (int32, -1 padding), `stm`
(integer 0/1), and `eval_cp` (finite white-relative labels). Each perspective
includes the enemy king and excludes its own king: the initial position has
31 active features. The manifest identifies STK-HalfKA, feature count, label
perspective, shard counts, SHA256 hashes and per-shard label statistics.
Shape, bounds, duplicate features, piece counts and hashes are checked before
training. These are encoding checks; the engine supplies game legality.

## Training and export

```bash
python tools/run_pipeline.py --data-dir runs/candidate/data \
  --workdir runs/candidate --epochs 20 --batch-size 4096 \
  --device cuda --engine build/bin/ChessEngine \
  --output artifacts/candidate.nnue
```

The command checks engine parity before copying the requested output. Add
`--tolerance-cp 0` for exact integer parity; the shared CLI default permits 1 cp.
The standalone exporter defaults to zero. Neither tolerance measures float
quantization loss or playing quality.
Use a classical, non-embedded engine for small-net parity: an embedded big net
would take precedence over `EvalFileSmall` during `eval`.

Re-running identical settings resumes `ckpt_latest.pt`, including optimizer,
scheduler and Torch RNG state. Dataset identity, width and training settings
must match. Completed training is reused only with matching settings and an
existing float checkpoint. CUDA OOM halves the batch, down to one; an OOM at
one raises instead of retrying forever.

For a fresh run from existing weights, use a new workdir with `--init`.
`--hidden 128 --teacher big/model_float.pt` trains the small net by distillation.
`--stage prep|train|export|verify|all` selects a stage. `--shard-slice start:stop`
selects a range of checked shards. Standalone export infers width from the
checkpoint and uses fixed engine scales; arbitrary legacy scale overrides
are unsupported.

```bash
python tools/nnue/train_vector64.py --dataset runs/candidate/data/manifest.json \
  --workdir runs/candidate --out-checkpoint artifacts/model_float.pt --device cuda
python tools/nnue/export_vector64.py --checkpoint artifacts/model_float.pt \
  --output artifacts/candidate.nnue --engine build/bin/ChessEngine
python tools/nnue/check_vector64.py artifacts/candidate.nnue
```

The standalone exporter checks layout and rejects non-finite weights. Passing
`--engine` also verifies integer inference and colour-mirror symmetry. Its
metadata records whether engine parity was requested.

## Selection and resource limits

The shared trainer reports training loss and saves the final model; it does not
automatically select a checkpoint on held-out validation. Reserve independent
validation positions/games, avoid overlapping sources between splits, and use
controlled matches for a strength decision. Bullet has a separate held-out
checkpoint-selection helper. Neither training loss nor bit-exact export proves
that a new model is stronger.

Feature-transformer parameters dominate memory: the big file is about 47 MB,
but floating weights, gradients, optimizer state, loaded shards and batches need
substantially more RAM/VRAM. Tune shard grouping and batch size for available
memory. Resume identity checks do not make runs across hardware/toolchain
versions automatically bit reproducible. Record the code revision, input hashes,
seed and environment. The shipped net's known/unknown provenance is in the
[model card](model-card.md).

## Self-play

For the native/UI commands, shard behavior and distinct resume contracts, use
the [data-generation walkthrough](datagen.md). The
[dataset/checkpoint reference](spec/datasets.md) defines stored shapes,
perspective, manifests and trust boundaries.

`tools/nnue/datagen_bulk.py` runs resumable, position-capped native datagen
chunks and records their hashes and settings. `tools/nnue/rl_loop.py` accumulates
native self-play, mixes optional Lichess anchor data, trains through the shared
pipeline and promotes only an SPRT-accepted candidate. Pass both `--engine`
and `--arbiter`; a match runner crash must not count as an SPRT rejection.

`tools/nnue/rl_train_vector64.py` is a separate experimental replay learner.
It uses the same STKNet/encoder/exporter, scores validator-supplied child
positions, and learns mover-relative targets. `--resume`/`--init` warm-starts
weights with a fresh replay buffer and optimizer; it does not restore an
interrupted replay experiment. Export its checkpoints with the same exporter.

`tools/run_training.ps1` accepts `-Data`, `-Workdir`, `-Engine`, `-Epochs`,
`-BatchSize`, `-Hidden`, `-Device` and optional `-Init`. It no longer assumes a
personal 80M dataset or manually tracks fixed shard slices.

Historical SPRT wrappers require `-Arbiter` and still compare their named
historical binaries. Those binary names do not represent current main.
The warm-history and lazy/dual wrappers remain option comparisons.

## Migration

`train_nnue.py`, `run_pipeline.py`, `train_vector64.py` and
`build_halfkp_npz.py` retain their command names as entry points into the shared
pipeline. Removed legacy CLI switches produce an argument error; use the
shared command's `--help` for the supported contract.

81920-feature HalfKP NPZ files and VECTOR64_NNUE checkpoints cannot be
reinterpreted as STK-HalfKA. Rebuild from raw labelled FENs and retrain.
Older STK-HalfKA manifests produced before format tags existed may be reused
with `--data-dir ... --allow-untagged-shards` after confirming their origin.
This opt-in still validates every shard. It must never be used to bypass
legacy HalfKP incompatibility.

The optional [Bullet float-transfer pipeline](bullet.md) shares the same STKNet
exporter and engine-parity gate. Its external checkout/toolchain is not pinned.
The [current referee limitation](limitations.md#material-adjudication) also
affects match-based promotion decisions.
