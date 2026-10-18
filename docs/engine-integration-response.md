# Engine integration guide

Use a process worker to answer chess queries or choose a move. The host owns
players, games, clocks, persistence and scheduling. The engine owns its current
position, rule queries and search state. Commands below run over stdin/stdout;
there is no native HTTP game-server API.

This guide replaces the old branch-specific integration discussion with current
behavior. Single-line requests, `children` and `SearchJson` are implemented.
The [validator protocol](validator.md) and [UCI reference](uci.md) define their
full command and reply contracts.

## Choose and initialize a worker

| Worker | Binary | Capability |
|---|---|---|
| Rules | `ChessEngine-validator` | Legal moves, FEN, child positions and status; rejects search. |
| Standard-chess AI | `ChessEngine-nnue` | UCI search with the embedded standard network. |
| Rules and variant AI | `ChessEngine-all` | Validator queries and search; drop variants use classical evaluation. |
| Rules and AI without an embedded net | `ChessEngine-variants` | Same variant interface; load a compatible net for standard chess if needed. |

Send `uci` and consume all replies through `uciok`. Check the options that the
actual binary advertises. Set variant/draw policy explicitly on variant workers,
then send `isready` and wait for `readyok`. A reused process retains options;
`ucinewgame` is not an option reset. Switching `UCI_Variant` resets the position
and search state, so select it before supplying a game position.

## Validate and apply a move

Prefer one self-contained line carrying both the move and its input position:

```text
apply e2e4 startpos
```

```json
{"ok":true,"legal":true,"fen":"rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1","sideToMove":"b","inCheck":false,"terminal":"none","capturedDropType":null}
```

For a persisted game, replace `startpos` with `fen <six fields>` and optionally
append `moves <move> ...` to supply history. Inline requests use scratch state:
even successful `apply` does not replace the worker's resident position. The
host commits the returned FEN to its own game state after accepting the reply.

Related requests:

```text
legalmoves startpos moves e2e4
children startpos moves e2e4
status startpos moves e2e4 e7e5
getfen startpos moves e2e4 e7e5
```

`children` returns a move and resulting FEN/status for every legal child in one
reply. For local branching this avoids a separate `apply` request per move.
A lone FEN does not contain repetition history; retain a base FEN plus moves
when the host needs repetition status.

Malformed inline input returns `ok:false` with `error:"malformed_request"`;
a parsed but illegal move returns `error:"illegal_move"`. Reject that operation.
The older two-line `position ...` followed by a query is supported, but failed
setup prints text and preserves old state. `readyok` does not confirm that a
position parsed successfully.

## Choose an AI move

Use a search-capable worker and an explicit budget. For independent requests,
set `Threads` and `Hash`, send `ucinewgame`, then supply the complete position:

```text
setoption name Threads value 1
setoption name Hash value 64
ucinewgame
position startpos moves e2e4 e7e5
go nodes 50000
```

Consume `info` lines until `bestmove`. Search is asynchronous; keep stdout
drained and enforce a host timeout. `stop` ends a running search and still
produces its final `bestmove`; `isready` is not a completion barrier.
[The Python client](examples.md) demonstrates bounded waits and
process cleanup.

On variant-capable search binaries, `setoption name SearchJson value true`
adds a JSON summary **after** `bestmove`. Read both before returning the worker
to its pool. The summary contains `bestMove`, `score`, `pv` and `depth`; a
positive score favors the root mover. `MultiPV` reports multiple candidates in
ordinary UCI `info` lines; the JSON summary is a single search result.

Node budgets can overshoot because checks are periodic. For reproducibility,
use one thread, matched reset/options/net state, and a fixed node/depth budget.
Timed and multi-threaded searches can choose different moves. Search strength
needs its own [match evidence](benchmark.md).

## Drop variants and partner transfers

Select `crazyhouse` or `bughouse` with `UCI_Variant`. Persist bracketed reserves
and `~` promoted markers in the FEN. For example, `[QPpp]` gives White a queen
and pawn, and Black two pawns. Drops use `P@e4` or `N@f7`.

In crazyhouse, a capture replenishes the capturer's local reserve. In bughouse,
it replenishes neither reserve on this board: route `capturedDropType` to the
partner board and inject updated reserves through a subsequent FEN. A captured
promoted piece reports pawn type `p`. The host must serialize cross-board
transfers and preserve the promoted marker through storage.

`DrawRules=variant` enables repetition/fifty-move checks for chess and crazyhouse
and disables them for bughouse. `DrawRules=standard` enables those per-board
checks for bughouse too. Choose the policy explicitly; this engine does not
implement sitting, partner coordination or a complete cross-board game result.
See [variant rules](variants.md). Keep `SyzygyPath` empty for drop-variant search;
the current probing path lacks a variant guard.

## Pooling, failures and adjudication

Use one in-flight request per worker. There are no request IDs for multiplexing.
Inline positions avoid resident-board leakage, but options remain shared process
state. Route UCI setup/search text separately from JSON query replies, and read
complete lines rather than assuming one OS read equals one response.

EOF, nonzero exit, timeout or a malformed response is a worker failure, not an
illegal chess move. Discard the result and replace the worker. Use a fresh
process after a failed network load; replacement is not transactional.

`status` and `canmate` currently use a defective mating-material heuristic.
They can label a mate-in-one position as insufficient material. `apply` checks
legality even after a draw label and does not enforce the host's finished-game
state. Keep game lifecycle and flag/claim adjudication in the host; these fields
are not a complete tournament referee. The counterexample and other boundaries
are recorded in [known limitations](limitations.md).

Pin and test the consumed engine revision: the JSON extension has no negotiated
schema version. See [compatibility](stability.md) and [executable documentation
checks](testing.md#python-tooling-and-training).
