# Bullet adapter for STK-HalfKA

This optional adapter trains float weights for the existing H=1024 STK-HalfKA
architecture, transfers them into `STKNet`, and reuses the PyTorch quantization,
export and integer-engine parity path. The [network contract](../../docs/vector64-spec.md)
owns the feature and binary format; this adapter changes neither.

The compatible external Bullet commit is not pinned here. The Rust files are
examples to register in a compatible Bullet workspace, not a standalone Cargo
package. Start with the fully local [CPU walkthrough](../../docs/nnue-training.md)
if you do not already have a working Bullet/CUDA environment.

## Setup and verification gates

Use a dedicated, disposable Bullet checkout, Rust and the full CUDA toolkit.
Register `stk_halfka.rs`, `stk_train.rs` and `stk_eval.rs` as examples in the
compatible workspace's `bullet_lib` manifest. Establish the required API and
toolchain from that checkout and record its commit with the run. Installing a
CUDA-enabled PyTorch wheel does not install that toolkit.

Build the conversion utility and check feature parity first:

```bash
# In the compatible Bullet checkout:
cargo build -r --package bullet-utils
cargo run -r --example stk_halfka > parity_rust.txt
# From the Vector-64 repository root:
python tools/bullet/parity_check.py /path/to/bullet/parity_rust.txt
```

The Python checker compares the Rust output with `halfka_features.py` on its
five fixed FENs. This checks the encoder against Python, not every C++ inference
path. Retain the output, including the black-to-move cases.

For a trained checkpoint, `stk_eval.rs` currently loads the hard-coded path
`checkpoints/stk-3`. Change that local example to the checkpoint being transferred
before building/running it. In the Bullet checkout:

```bash
cargo run -r --example stk_eval --features cuda > bullet_evals.txt
```

From this repository, transfer the **same** checkpoint:

```bash
python tools/bullet/transfer_to_stknet.py --raw /path/to/bullet/checkpoints/stk-10/raw.bin --workdir runs/bullet-check --engine build/bin/ChessEngine --bullet-evals /path/to/bullet/bullet_evals.txt --tolerance-cp 0
```

Check that the oracle file contains all five finite `EVAL<i>` values. The
transfer script ignores other lines and does not reject an empty oracle file.
For parsed values it permits up to 0.5 cp float-transfer difference.
`--tolerance-cp 0` separately requires exact integer-engine parity after export;
its default is 1 cp. These gates do not measure held-out loss or playing strength.

## Build a candidate

Generate three-field `<fen> | <eval> | <wdl>` text through native datagen or
`datagen_bulk.py --emit raw`. Evaluation and WDL labels are White-relative;
the held-out helper converts them to the mover's perspective. Use at least
two shards: the wrapper reserves the final lexically sorted shard for validation.
Avoid overlapping games/positions between that shard and training data.

```bash
python tools/bullet/build_net.py --bullet /path/to/bullet --data-dir runs/bullet-data --scratch runs/bullet-scratch --workdir runs/bullet-model --engine build/bin/ChessEngine --epochs 10
```

MSVC paths include `bin/Release/`; Windows executable names end in `.exe`.
The wrapper converts, interleaves and shuffles the training shards. It runs
`stk_train`, compares saved checkpoints on held-out loss, and transfers/exports
the selected checkpoint to `runs/bullet-model/stk_halfka_1024.nnue`.

The Rust trainer fixes batch size at 16,384, WDL blend at 0.5, evaluation scale
at 400, cosine learning-rate decay, and checkpoint save rate at five superbatches.
The wrapper's `--epochs` is passed as a superbatch count; batches per superbatch
are `max(1, positions // --batch)`. Its `--batch` setting does **not** change the
Rust trainer's batch size, so leave it at 16,384. A nominal pass may omit the
remainder; this is not an exact once-per-row epoch contract.

`pick_checkpoint.py` defaults to a seed-12345 sample of up to 50,000 held-out
positions and selects the minimum squared sigmoid loss among available
`checkpoints/stk-*/raw.bin` files. It loads the held-out text and tensors into
memory. Selection is a separate post-training step; the Rust `LocalSettings`
has `test_set: None`.

**Run isolation matters.** The wrapper reuses nonempty intermediates and a
matching final checkpoint by existence, without proving data/settings identity.
If the expected final checkpoint is absent, it removes the external checkout's
shared `checkpoints/stk-*` directories before training. Use a disposable checkout
and fresh scratch/work directories for changed inputs. `--keep-scratch` retains
the converted/interleaved files; otherwise those intermediates are deleted after
`train.bin` is ready. These are weaker resume guarantees than the shared Python
pipeline's manifest/settings contract.

After selection and parity, run [controlled matches](../../BENCHMARK.md) with an
identified baseline, explicit validator, and recorded seeds/budgets. The wrapper's
printed historical `runs/v2` comparison is not a current baseline prescription;
its printed match command also omits the now-required `--arbiter`.

## Feature mapping

The adapter implements `32 * 11 * 64 = 22528` features per perspective. Black
perspectives flip ranks; king files e-h trigger a file mirror; own kings are
omitted and enemy kings are kept. The index is
`(king_bucket * 11 + piece_kind) * 64 + oriented_square`.

The custom input assumes `bulletformat::ChessBoard` iterates a mover-relative
record: `piece & 8 == 0` identifies the mover, a set bit identifies the opponent,
and `piece & 7` gives types 0-5, pawn through king. The non-mover perspective
rank-flips those squares. Check
this external-format assumption on the chosen Bullet revision.

The paired sparse-input callback needs one index for each perspective. For an
own king, the adapter emits sentinel index 22528 in that perspective and the
real enemy-king feature in the other. Each valid board contributes exactly one
sentinel row per perspective. Transfer adds its FT weight to the FT bias and
then removes the sentinel row. Its PSQT contribution, like the PSQT bias, cancels
between the two perspectives. STKNet instead has a leading padding row at index
zero, so real feature rows shift by one during transfer; binary export removes
the padding row again.

## Float checkpoint layout and scaling

`stk_train.rs` declares this `save_format` order. For H=1024, `raw.bin` is
23,386,776 native float32 values (93,547,104 bytes), without a header:

| Tensor | Number of float32 values |
|---|---|
| `l0w`, `l0b` | `22529 * 1024`, `1024` |
| `l1w`, `l1b` | `128 * 1024`, `128` |
| `l2w`, `l2b` | `256 * 16`, `256` |
| `l3w`, `l3b` | `8 * 32`, `8` |
| `psqtw`, `psqtb` | `8 * 22529`, `8` |

The transfer interprets affine weights as column-major `(out, in)`, reshaping
raw storage to `(in, out)` before transposition. It checks the float count;
there is no embedded architecture/version/provenance header.

| STKNet parameter | Transfer |
|---|---|
| `ft.weight[f+1]` | `l0w.reshape(22529,1024)[f]`, for real features |
| `ft_bias` | `l0b + l0w.reshape(22529,1024)[22528]` |
| `l1w` | `l1w.reshape(1024,128).T.reshape(8,16,1024) * (128/127)` |
| `l1b` | `l1b.reshape(8,16)` |
| `l2w`, `l2b` | `l2w.reshape(16,256).T.reshape(8,32,16)`, `l2b.reshape(8,32)` |
| `outw`, `outb` | `l3w.reshape(32,8).T * (400/508)`, `l3b * (400/508)` |
| `psqt.weight[f+1]` | `psqtw.reshape(22529,8)[f] * 400`, for real features |

The factors use default `eval_scale=400`, `OUT_CP=508`, and STKNet's
`PAIR_FACTOR=127/128`. Keep the scale consistent across Rust training, held-out
selection, oracle comparison and transfer. Do not infer successful transfer
from matching dimensions alone.

## Graph correspondence

| STKNet operation | Rust graph |
|---|---|
| Shared FT for both perspectives | `new_affine("l0", 22529, 1024)` |
| Clip each accumulator half to 0..1, multiply matching halves | Explicit `l0.slice(...).forward(...).crelu()` halves and elementwise multiplication |
| Concatenate mover/opponent 512-element vectors | `stm_h.concat(ntm_h)` |
| Eight bucketed 1024→16→32→1 dense stacks | Affine output banks, `select(buckets)`, CReLU after the first two layers |
| Mover-minus-opponent PSQT side output | Shared sparse affine to eight values, bucket selection and subtraction |
| Bucket | `min((piece_count - 1) / 4, 7)` on valid boards |
| Training objective | Squared error after sigmoid, with blended WDL/evaluation targets |

CReLU clips to 0..1; the graph does not square each clipped activation. The
integer exporter applies the fixed quantization and shifts in the network
contract. Record feature, float-transfer and integer-parity results for the
actual external revision instead of treating historical verification as
certification of a new toolchain.
