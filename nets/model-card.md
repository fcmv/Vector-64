# Shipped STK-HalfKA model

This card records what can be established from the committed artifact and
current implementation. Missing training history is left explicit.

## Identity

| Field | Value |
|---|---|
| File | `nets/stk-vector-64.nnue` |
| Size | 46,997,305 bytes |
| SHA256 | `7b877e6bdefde3b41ef958e3270b3312806382a1e97d5e24f0c0c6217cd87ace` |
| Magic / version | `STKHALFKA` / 1 |
| Features | 22,528 per perspective |
| Accumulator width | 1024 |
| Output buckets | 8 |
| Output convention | Side-to-move integer centipawn estimate, integrated PSQT side output |
| Runtime | Current `src/nnue/halfka.h`, `network.h`, and `network.cpp` |

The model architecture is the existing
[STK-HalfKA contract](../docs/vector64-spec.md). This documentation does not
change it. A separate optional 128-wide model can be loaded through
`EvalFileSmall`; no small weight file is shipped alongside this artifact.

The embedded network in the published v1.0.0 Windows `-nnue.exe` is byte-for-byte
identical to this file. That executable is the fixed architecture baseline;
the network contract records its executable hash and source tag. This establishes
release artifact identity, not the missing training provenance described below.

## Use and evaluation

The big model is embedded in `ChessEngine-nnue`, `ChessEngine-all`, and the
visualizer when built with the default `EMBED_NNUE`. Standard chess uses it;
drop variants suppress it because reserves and drop updates are not represented.
It can also be loaded into the classical executable with `EvalFile`.

Validate layout with `python tools/nnue/check_vector64.py nets/stk-vector-64.nnue`.
Scalar/SIMD and incremental/full inference checks constrain runtime consistency.
The `NODES_NNUE` entry in `tools/bench_signature.txt` fingerprints the combined
search plus these weights, not model strength independently.

No absolute rating, held-out accuracy score, or reproducible full-training report
is attached to this weight file. Export parity establishes execution consistency,
not prediction quality or playing strength. Scores are not calibrated win odds.

## Provenance available in this repository

The current training and Bullet-transfer code can produce the supported format.
However, the shipped file has no adjacent manifest identifying its exact
training source commit, raw data hashes/licenses, checkpoint, seed, optimizer
history, hardware, or selection run. Those details cannot be recovered from the
binary header and are not asserted here. The [training guide](../docs/nnue-training.md)
describes current tooling, not a proven reconstruction of this artifact's run.

The root repository is Apache-2.0, but no separate model-specific terms or input
provenance record accompany the weights. This card supplies no additional
license grant or claim about unknown training-data rights. Consult the maintainer
and [component notices](../THIRD_PARTY_NOTICES.md) when establishing redistribution
terms for a downstream model package.

## Replacement record

A replacement should record the byte hash, code revision, data/source rights and
hashes, preprocessing/label perspective, training configuration, checkpoint
selection, integer parity results, controlled match conditions and outcome.
Update this identity and regenerate the NNUE benchmark signature with the weight
change. Do not present a new file's results under the previous file's hash.
