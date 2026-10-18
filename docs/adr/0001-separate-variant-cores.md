# Separate variant cores

## Context

Drop variants need reserves, promoted tracking, different hash state, and wider
move lists. Adding runtime variant checks to every standard move/update would
change the layout and hot paths of the ordinary chess engine.

## Decision in the current code

CMake compiles core sources separately as `chess_core` and
`chess_core_variants`, defining `ENGINE_VARIANTS` for the latter. Standard builds
omit variant position fields and use 256-entry move lists; variant builds use
512. Variant identity remains runtime-selectable inside the variant build.

## Consequences and checks

Build time increases, while tournament binaries avoid reserve branches/state.
Variant state tests cover drops/hash/undo. Both standard benchmark signatures
must remain unchanged for a variant change intended to preserve standard search.
Intentional search/net changes use the explicit regeneration policy instead.

References: `CMakeLists.txt`, `src/cores/position.h`, `src/cores/move.h`,
`tests/cpp/test_variants.cpp`.
