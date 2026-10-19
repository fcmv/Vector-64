# Dataset and checkpoint contracts

The owning code is `tools/nnue/build_stk_data.py`, `contracts.py`, `make_net.py`
and the native writer in `src/datagen/selfplay.h`. This page describes current
formats, not an architecture migration. [Generation](../datagen.md) and
[training](../nnue-training.md) provide runnable workflows.

## Text labels

| Form | Interpretation |
|---|---|
| `<fen> \| <cp>` | Label perspective is selected by `--cp-source`; default White. |
| `<fen> \| <cp> \| <wdl>` | Native/Bullet-style row; WDL is a White game outcome. |
| Lichess evaluation JSONL, optionally zstd | Select qualifying evaluation by depth/knodes; retain source provenance. |

Native raw output is White-relative for both cp and WDL. Do not infer perspective
from the FEN's mover. For a Black-to-move position labelled +100 White cp, the
trainer's mover-relative target is -100. Training performs that sign conversion
once; the exported engine does not apply another label conversion.

WDL mixing uses `p = (1-lambda) * sigmoid(cp/400) + lambda * wdl`, then maps
probability back through `400 * log(p/(1-p))`, with implementation clamps near
0/1. Already-blended two-column labels must not be blended again. Mate mappings,
cp filters, source-perspective conversion and deduplication are preparation
settings, not properties that can be recovered from a weight file.

## Prepared NPZ shards

Each row represents one standard-chess position under STK-HalfKA.

| Array | Shape | Meaning |
|---|---|---|
| `white_indices` | `[N, max_features]` | White perspective feature indices; integer, generated as int32. |
| `black_indices` | Same | Black perspective feature indices. |
| `stm` | `[N]` | Integer 0 White / 1 Black. |
| `eval_cp` | `[N]` | Finite White-relative labels. |

Valid feature indices are 0..22527; -1 is padding. There are 1..31 active
features per perspective, with no duplicates. The initial position has 31,
because the enemy king is included and the own king is excluded. The producer
defaults to 32 columns; the validator accepts compatible wider padding and
integer dtypes rather than requiring an exact int32 file encoding.

`np.load(..., allow_pickle=False)` reads shards. Validation checks array shape,
integer indices, padding/feature counts, mover values, finite labels and
manifest counts/hashes. Feature decoding validates representation, not complete
game reachability. Independent engine legality checks remain a separate stage.

## Manifest

The current manifest has `format: "STK-HalfKA"`, `version: 1`,
`features: 22528`, `target_perspective: "white"`, `max_features`,
`total_samples`, `shards`, `prep_config` and aggregate `stats`.
The producer writes each shard's basename `file`, positive `samples`, SHA256 and
label statistics. Validation checks a SHA256 when present; it accepts manifests
without that field, so retain the producer's hashes when distributing a dataset.
Names must be unique; summed shard counts must equal `total_samples`.

Preparation writes source paths/sizes/mtimes and options into `prep_config`.
These identities help detect changed inputs; they are not a complete immutable
raw-source hash/provenance archive. Store source byte hashes and rights records
separately for a published training run. A Hugging Face identifier also needs
an identified dataset revision to establish a historical input.

`progress.json` checkpoints completed preparation shards. Resume validates
saved settings and shard hashes and replays input after the saved line boundary.
Deduplication's global scope uses SQLite. Use a new directory for a changed
source/filter/encoding configuration; do not rewrite the manifest to silence
an identity failure. Only explicitly known pre-tag STK-HalfKA data can use
`--allow-untagged-shards`; 81920-feature HalfKP arrays remain incompatible.

## Float and training checkpoints

`model_float.pt` stores the supported STKNet state dict, format and hidden width.
Resumable `ckpt_latest.pt` additionally stores model, optimizer, scheduler,
training position and Torch RNG state, with compatible settings required.
`--init` is a warm start in a new run; it is not a replacement for resume.
The experimental replay learner has a separate lifecycle and does not restore
its replay experiment from a supervised checkpoint.

Checkpoint loading currently permits Python pickle deserialization. Load only
trusted files. A valid tensor shape does not establish a trustworthy origin.
Export removes the embedding padding row and uses the fixed integer scales in
[the network contract](../vector64-spec.md). Export metadata identifies the
checkpoint/network and whether parity was requested; it is not a training-data
rights declaration, held-out evaluation or strength certificate.

## Release evidence for a trained model

Preserve source revisions and raw input hashes/rights, splitting and filtering,
seed, dependency versions, optimizer settings, checkpoint-selection rule,
float/quantized validation, exact integer parity, mirror checks and match setup
with its result. The [shipped model card](../model-card.md) marks information
not available for the existing weights. Unknown history must remain unknown.
