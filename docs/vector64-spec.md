# STK-HalfKA network contract

The fixed architecture baseline is the published **v1.0.0 Windows NNUE
executable**, `STK-Vector-64-windows-x86-64-avx2-nnue.exe`. Its release tag points
to `b301d4fea0faf08fa2cf774438b532b027503fd7`. The current
`src/nnue/halfka.h` and `network.h` implement the same feature set, topology,
integer arithmetic and file layout. Runtime refactors and training-tool changes
in the checkout do not define a replacement architecture.

The downloaded executable's SHA256 is
`a71393ffb82c26ac3026b7d9d821de3d74230ef533529d9d582fb6067adf4596`.
Its embedded 46,997,305-byte big net exactly matches the repository's shipped
file, whose identity is in the [model card](model-card.md). The unsuffixed
Windows `.exe` is the classical build; `-nnue.exe` is the embedded-network build.
See the [v1.0.0 release](https://github.com/fcmv/Vector-64/releases/tag/v1.0.0).

The former 81920-feature VECTOR64_NNUE format is unsupported by this release
and the current engine.

## Features and model

There are 32 king buckets, 11 piece kinds and 64 squares: 22528 features per
perspective. Black perspectives flip ranks. Kings on files e-h cause a file
mirror; the transformed king selects `(rank * 4 + file)` as its bucket.
Own pawns through queens use kinds 0-4; enemy pawns through kings use 5-10.
Own kings are excluded. The index is `(king_bucket * 11 + kind) * 64 + square`.

The accumulator width H is 1024 (big) or 128 (small). Clipped 0-127 accumulator
halves multiply pairwise and shift right seven bits, then mover/opponent
vectors concatenate to H elements. Each of eight output buckets has layers
H -> 16 -> 32 -> 1. The hidden dense layers shift right six bits and clip to
0-127. The final dense result shifts right four bits. The separately
accumulated mover-minus-opponent PSQT result also shifts right four bits and
is added. The bucket is `clamp((piece_count - 1) / 4, 0, 7)` with integer division.
Output is side-to-move relative, without an extra classical PSQT blend.

## Worked feature example

At the initial position, White's king on e1 mirrors to d1, selecting bucket 3.
The own pawn on a2 mirrors to h2 (square 15), giving
`(3 * 11 + 0) * 64 + 15 = 2127`. The pawn on h2 mirrors to a2 (square 8),
giving index 2120. The enemy king on e8 mirrors to d8 (square 59), kind 10,
giving `(3 * 11 + 10) * 64 + 59 = 2811`. The own king contributes no feature.
There are 31 active indices per perspective at start position, not 30.

The big file is the shipped architecture. H=128 is the already-implemented
optional small-network width; this documentation proposes no architecture change.
[Engineering](implementation/engineering.md) explains accumulator ownership.

## Binary layout

All numeric fields are little-endian, tightly packed, with no padding.

| Field | Type / shape |
|---|---|
| magic | 9 bytes: `STKHALFKA` |
| version | uint32: 1 |
| features | uint32: 22528 |
| hidden | uint32: 1024 or 128 |
| buckets | uint32: 8 |
| FT weights | int16[22528, H] |
| FT biases | int16[H] |
| PSQT weights | int32[22528, 8] |

For each bucket 0-7, append in order:
`int8[16,H] l1w`, `int32[16] l1b`, `int8[32,16] l2w`,
`int32[32] l2b`, `int8[32] outw`, `int32 outb`.

The header is 25 bytes. Total sizes are 46,997,305 bytes for H=1024 and
6,510,649 bytes for H=128. `check_vector64.py` validates header and exact size;
`--allow-trailing` explicitly permits extra bytes.

## Float checkpoints and quantization

STKNet float checkpoints store a `state_dict` (resumable trainer checkpoints
store `model`). The FT and PSQT embeddings have one leading zero padding row;
export removes it. FT weights/biases scale by 127, dense weights by 64,
dense biases by 8128, and PSQT by 16. Values round and clip to engine ranges.
NaN and infinity are rejected. Width is inferred from FT weights.

The exporter shares `make_net.quantize_model` with the integer Python oracle.
Engine parity evaluates labelled test positions and their colour mirrors;
matching the integer oracle and mirror symmetry gates the full pipeline.
No conversion from old HalfKP checkpoint tensors is provided.


## Loader and verification boundaries

The Python checker requires the exact packed size unless `--allow-trailing` is
explicit. The C++ loader currently accepts trailing data and reads integer
fields in host order; supported release targets are little-endian. A failed
payload read is not transactional and can corrupt a loaded model; see
[limitations](limitations.md#network-replacement).

Use `--tolerance-cp 0` in the shared training CLI when claiming exact integer
parity. Its default permits 1 cp; standalone export defaults to zero. Color-mirror
symmetry is checked independently. Float-model drift is reported separately and
is not evidence that the integer paths disagree.
