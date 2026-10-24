# Known limitations

This describes current behavior and known defects. It does not promise future
features or assign roadmap priority. A result that violates a documented
contract is a defect even if another engine path produces the same result.

## Material adjudication

The current `canmate` and `draw_insufficient_material` logic uses a material
heuristic, not a complete possible-mate/dead-position analysis. It ignores some
opponent blockers and bishop-color constraints.

Concrete counterexample:

```text
status fen 7k/5K1n/7B/8/8/8/8/8 w - - 0 1
canmate w fen 7k/5K1n/7B/8/8/8/8/8 w - - 0 1
apply h6g7 fen 7k/5K1n/7B/8/8/8/8/8 w - - 0 1
```

The first two report insufficient material / `canMate:false`, although the
third legally delivers mate. Do not use these material fields as the sole
source of automatic game or flag adjudication. This also affects any tooling
that treats validator terminal status as its referee; it is not a UI-only issue.

The API's draw labels implement its own per-board automatic status policy;
claimable draws, fivefold/75-move rules, and general dead-position reachability
are not a complete FIDE tournament-adjudication implementation.

## Network replacement

A valid header followed by truncated payload can overwrite active network
storage before loading fails. If a net was already loaded, the object can still
report itself loaded after that failure. Replacing a net is not transactional.

Validate candidate files first and use a fresh engine process per candidate.
After `EvalFile load failed` or `EvalFileSmall load failed`, discard that process
rather than assuming the old net remains intact. A header/size check establishes
layout, not provenance, quality, or safe numeric ranges for arbitrary hostile
weights. PyTorch checkpoints must come from a trusted source: the current
training loader uses pickle-capable `torch.load(..., weights_only=False)`.

## Protocol and state

A bad two-line `position` setup prints a UCI diagnostic and retains the previous
position. A later query can succeed against that old state. Prefer the
[self-contained validator form](docs/validator.md#self-contained-requests).

There is no request-ID multiplexing or negotiated JSON schema version. Use one
request at a time per process, bounded waits, and a pinned/tested engine build.
`internal_error` is reserved; crashes, EOF and timeouts are actual fault signals.
`apply` does not enforce the host's already-finished-game state.

## Variants

Crazyhouse and bughouse share drop-board mechanics, not all reserve semantics.
Bughouse captures are transferred by a host to a partner board. This engine
implements no partner coordination, sitting, shared clock policy, or cross-board
transaction protocol. A standalone bughouse match without incoming material
cannot assess realistic drop play.

Drop variants use classical evaluation. The fixed current standard NNUE has no
reserve features or drop update path. SEE does not fully model reserve material,
and variant strength depends on the tested budget/opponent/setup. No absolute
public rating is established by the repository's relative self-play numbers.

## Search and reproducibility

Single-thread fixed-budget tests require identical binary, net, options,
position/history and reset state. Persistent TT/ordering state can change later
searches. Wall-clock budgets and Lazy SMP scheduling are not deterministic.
Scalar/SIMD equality applies to integer evaluation, not all timed search results.

The node limit is checked periodically. A requested node count is a stopping
budget, not a promise that the final counter equals that count exactly.
TT replacement and probe snapshots use striped locks in multithreaded search;
sampled helper counters use atomics. Passing the current tests does not establish
race freedom for unrelated shared engine/session state or every SMP interleaving.

## Tablebase search

Syzygy probing is disabled for drop-variant roots on every search worker.
A low on-board piece count does not make a reserve position a valid
standard-chess tablebase position.

Root ranking preserves UCI `searchmoves` and selects the best-ranked moves
within that allowed set, even when the caller excludes all globally optimal
moves. DTZ receives whether any position repeated since the last capture or
pawn move. A FEN alone cannot reconstruct that history; supply the game moves
when repetition matters.

Missing DTZ files fall back to WDL ranking, which does not provide DTZ progress
guidance. Missing WDL coverage falls back to normal search. The external-file
regression test is opt-in through `STK_SYZYGY_TEST_PATH`; a test run without
that data does not establish real table-file coverage. See the
[Syzygy reference](third_party/fathom/README.md).

## Platforms and browser use

MSVC builds require AVX2 even with `ENGINE_NATIVE=OFF`. Native Unix builds default
to machine-specific tuning unless disabled. ISA compatibility and operating-system
runtime compatibility are separate requirements.

The pthread WASM build needs cross-origin isolation and SharedArrayBuffer. It
has no single-thread fallback when those are unavailable. Service workers need
a secure context (localhost is suitable for development). Native visualization
continues to use its local HTTP transport.

The native visualizer binds loopback and is unauthenticated. Its control API can
load network paths and write datasets/recordings with the process's permissions.
Do not expose it through a public proxy as if it were a hosted multi-user service.

## Visualizer state publication

Pausing sets the session flag without immediately publishing a new snapshot.
If no later publication occurs, the browser can keep showing the old pause
button/status and disabled step control while play has actually paused. An
explicit `pause` control with `value:false` can resume the native session;
do not infer paused state solely from a stale button. A successful control
reply does not guarantee that the requested state has already been published.

The node/delay input fields initialize to UI defaults and may differ from CLI
overrides until explicitly changed. Set those controls before recording a demo
or interpreting the configured budget. The native JSONL recorder appends to an
existing file; choose a fresh filename when a separate recording is needed.
Recordings contain summaries rather than full activation frames or screen video.

## Training and evidence

Integer export parity and dataset integrity do not establish playing strength.
The shared supervised trainer currently writes the final checkpoint without an
automatic held-out checkpoint-selection stage. Use independent validation data
and controlled matches before replacing the shipped network.

The optional Bullet adapter needs an external checkout with examples registered.
Its compatible upstream revision is not pinned in this repository. Its build
script reuses outputs by existence and can remove shared `checkpoints/stk-*`
directories. Use a disposable, dedicated Bullet checkout and isolated scratch
paths; do not treat it as a fully reproducible package installer.

The embedded net has a known byte identity but incomplete recorded training
provenance. See the [model card](nets/model-card.md). Component licensing is
mixed; see [third-party notices](THIRD_PARTY_NOTICES.md) before redistribution.
