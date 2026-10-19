# Engineering guide

Use this guide to locate a change and its verification. Observable behavior is
specified in the [engine contract](../spec/engine-contract.md),
[UCI](../uci.md), [validator](../validator.md), and
[STK-HalfKA](../vector64-spec.md) references. A disagreement between those
contracts, code, and tests is a defect to resolve explicitly.

## Repository map

| Concern | Files |
|---|---|
| Executable modes and embedded-net entry | `app/main.cpp` |
| Types, bitboards, move encoding and lists | `src/cores/types.h`, `bitboard.h`, `move.h` |
| Board, FEN, make/unmake, history and material | `src/cores/position.{h,cpp}`, `material.h` |
| Non-sliding/sliding attacks and geometry | `src/cores/attacks.{h,cpp}` |
| Legal/pseudo-legal moves and drops | `src/cores/movegen.{h,cpp}` |
| Hash keys | `src/cores/zobrist.{h,cpp}` |
| Input parsing, options, scheduling and output | `src/uci/uci.cpp`, `uci_util.h` |
| Structured validator replies | `src/uci/validator.h` |
| Search, quiescence, SMP and evaluation selection | `src/search/search.{h,cpp}` |
| TT layout, replacement and bounds | `src/search/transposition_table.h` |
| Ordering/history/SEE | `src/search/move_ordering.{h,cpp}` |
| Network ownership and non-search evaluation | `src/search/evaluator.{h,cpp}` |
| Feature indexing, integer kernels, accumulators | `src/nnue/halfka.h`, `network.{h,cpp}` |
| Syzygy adapter and vendored prober | `src/search/syzygy.{h,cpp}`, `third_party/fathom/` |
| Native self-play and shard output | `src/datagen/` |
| Pure telemetry, session, wire and transport | `src/viz/` |
| UI, decoder and source adapters | `ui/src/` |
| Shared training/data/model/export contracts | `tools/nnue/` |
| Bullet adapter and weight transfer | `tools/bullet/` |

## Position transitions

`Position` owns board bitboards and a mailbox, side to move, castling rights,
en passant, clocks, hash, running material/PSQT, and repetition history. Variant
builds add reserves, promoted-square tracking, reserve material, and rule policy.

`make_move` changes this state and fills `UndoInfo`. `unmake_move` restores it.
`key_after` predicts the child key for TT prefetch; it must agree with the hash
after the real move, including captures, promotions, castling, en passant, and
drops. A source square on a drop is a piece code, so code accessing the moving
piece should use the appropriate move-aware helper rather than mailbox lookup.

A FEN round trip reconstructs board state but does not reconstruct repetition
history. Tests compare incremental fields with a rebuilt position, and separately
check exact undo state and history. A matching incremental hash is necessary
but not sufficient evidence that a move is legal.

## Search lifecycle

`EngineUci::handle_position` parses into a temporary position and commits only
on success. A failed setup retains the old resident position and prints a UCI
diagnostic. Inline validator requests use a scratch position and return JSON
errors. Prefer them when constructing a stateless worker adapter.

`handle_go` parses budgets and starts a search on a root copy. Search callbacks
publish completed iterations and enforce dynamic time management. `stop_and_join`
coordinates output and teardown; active search IDs prevent superseded work from
publishing as the current request. Never assume that a `readyok` means an active
search has completed: completion is signalled by `bestmove` or a joined stop.

`ucinewgame` resets the position and clears search state. History ordering can
persist across searches within a game through `PersistOrdering`; this affects
reproducibility. A fixed-node comparison should start with matched process,
option, network, and reset state.

## Inference lifecycle

The evaluator owns big and optional small weights. The primary accumulator stack
and refresh state belong to each search worker. Move deltas update non-king
features; king-orientation changes introduce refresh boundaries. Special moves
must remove/add the actual affected pieces, not just the move endpoints.

Search `eval_pos` selects classical lazy evaluation, an on-demand small-net
refresh, or the big-network path. The non-search `eval` route rebuilds its own
accumulator and does not exercise every lazy/dual selection policy. Use the
classical executable for isolated small-net parity so an embedded big net does
not take precedence.

Network reload failure is currently not transactional: see
[limitations](../limitations.md). Do not infer a successful rollback from a
`load failed` diagnostic. This documentation change does not change model
architecture or the loader implementation.

## Invariants and their checks

| Invariant / boundary | Check |
|---|---|
| Legal tree agrees with known reference counts | `perft.*` CTest cases and `test_data/standard.epd` |
| Incremental board/hash/material state matches reconstruction and undo | `consistency.make_unmake_and_movegen` |
| Integer SIMD inference and accumulator updates agree with reference paths | `consistency.nnue_simd_bitexact`; `tests/cpp/test_zobrist.cpp` |
| Variant reserve/promoted/drop state and perft anchors | `variants.drops_state_and_perft` |
| Search/net fingerprint for a fixed configuration | `tools/bench_signature.sh` and central `bench_signature.txt` |
| Exported checkpoint agrees with integer inference | CPU training/parity tests and `make_net.stage_verify` |
| Dataset shapes, perspective, identity and finite values | `tools/nnue/contracts.py` and NNUE data tests |
| Telemetry equals a separate engine forward pass | `viz.telemetry_exact` |
| Session state follows its emitted move sequence | `viz.session_selfplay` and variety/shard tests |
| C++ wire matches the TypeScript decoder | `viz.wire_fixture`, `VIZ_FIXTURE` UI tests |
| Tournament targets exclude visualization dependencies | CI checks their link commands |
| Published examples and option tables agree with binaries | `tests/docs/test_examples.py` |

These checks establish their tested properties. The material-adjudication
counterexample in [limitations](../limitations.md) demonstrates why agreement
between engine paths alone cannot certify an entire rules surface.

## Review boundaries

For a change to search or weights, state why a signature change is expected and
supply appropriate strength evidence. For a semantics-preserving refactor, both
fingerprints should remain unchanged. Never hand-edit the central counts.

For a new visualization C++ source, check both native CMake and the explicit
WASM link list. For an encoder change, rebuild the C++ fixture and run the UI
wire test. For UI edits, rebuild the committed HTML using the CI Node toolchain.

[Contributing](../contributing.md) and [testing](../testing.md) give the commands.
