# Existing STK-HalfKA contract

## Context

Feature indexing, integer quantization and evaluation perspective must agree
between data, training, export and runtime. A file with the same suffix can
still describe a completely different network.

## Decision for the current documentation baseline

Use the published v1.0.0 Windows `-nnue.exe` as the fixed architecture baseline.
Its embedded model matches the repository's shipped net byte for byte; release
identity is recorded in the [network contract](../vector64-spec.md).
Document that architecture: 22,528 features per perspective,
1024/128 accumulators, pairwise clipped activations, eight 16/32/1 dense heads,
and the integrated PSQT side output. Keep its `STKHALFKA` v1 packing and
mover-relative output explicit. This work does not change feature or layer design.

Drop variants suppress that standard network because it cannot represent hands
and its accumulator has no drop path. The network remains loaded for a switch
back to chess. Classical PSQT is not blended into a normal NNUE result.

## Consequences and checks

Data manifests identify the feature/perspective contract. Old HalfKP tensors
cannot be reinterpreted. Integer exporter/runtime parity and scalar/SIMD checks
constrain encoding and arithmetic; playing quality requires separate evidence.
A loader failure is a known defect, not a different architecture contract.

References: [network specification](../vector64-spec.md), `src/nnue/halfka.h`,
`src/nnue/network.h`, `src/search/evaluator.cpp`, `tools/nnue/make_net.py`.
