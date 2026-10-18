# Telemetry outside search

## Context

Detailed activations and contribution edges are useful in a visualizer but would
add work and dependencies to tournament search if captured at every node.

## Decision in the current code

`Viz::capture` builds a separate accumulator and forward pass for snapshots.
`chess_viz` and the native HTTP/UI transport are separate targets. The UI consumes
the C++ encoder's framed binary output through native HTTP or WASM adapters.
The ordinary engine targets do not link HTTP/JSON/UI components.

## Consequences and checks

Telemetry tests require exact eval and attribution agreement. Native and TS
wire fixtures constrain the boundary. CI checks engine link dependencies and
search fingerprints. WASM explicitly lists visualization sources in its shell
linker script, so new shared sources must be added there as well as to CMake.
The current WASM build needs pthread isolation and has no scalar-thread fallback
when SharedArrayBuffer is unavailable.

References: `src/viz/probe.cpp`, `wire.cpp`, `session.cpp`, `tools/build_wasm.sh`,
[visualizer reference](../visualizer.md).
