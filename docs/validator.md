# Validator protocol

The custom position-query interface is available in variant-capable binaries:
`ChessEngine-validator`, `ChessEngine-variants`, and `ChessEngine-all`.
The dedicated validator starts without an embedded net, with one thread and a
1 MB TT; `go` and `bench` are refused. Search/UCI support and protocol queries
are separate capabilities.

Each successful query emits one compact JSON line. Setup and health commands
remain UCI text. Source: `src/uci/uci.cpp` and `src/uci/validator.h`.

## Self-contained requests

Prefer a request carrying its own position:

```text
legalmoves startpos
status startpos moves e2e4 e7e5
apply e2e4 startpos
getfen fen 7k/8/8/8/8/8/8/K5R1 w - - 0 1
canmate w startpos
children startpos
```

Grammar:

```text
getfen    [position-clause]
legalmoves [position-clause]
children  [position-clause]
status    [position-clause]
apply <uci-move> [position-clause]
canmate <w|b|white|black> [position-clause]
position-clause := startpos [moves <move> ...]
                 | fen <six-FEN-fields> [moves <move> ...]
```

Use one request at a time per process. Inline requests operate on a scratch
position and never replace the resident position, including inline `apply`.
Variant and draw-policy options still belong to the process: set them explicitly
before dispatching work to a reused worker.

Without a clause, queries use the resident position set by `position ...`, and
`apply` mutates that resident position. If two-line setup fails, the old position
remains and the failure is text, not JSON. `isready` does not acknowledge a
successful parse. This is why the self-contained form is safer for host adapters.

## Replies

| Command | Success fields after `ok:true` |
|---|---|
| `getfen` | `fen:string`, `variant:chess/crazyhouse/bughouse`, `drawRules:standard/variant` |
| `legalmoves` | `count:integer`, `moves:string[]` |
| `children` | `count:integer`, `children:object[]`; each child has `move`, `fen`, `sideToMove`, `inCheck`, `terminal` |
| `status` | `sideToMove:w/b`, `inCheck:boolean`, `terminal:string`, `legalCount:integer`, `repetitions:integer` |
| `apply` | `legal:true`, `fen`, `sideToMove`, `inCheck`, `terminal`, `capturedDropType` |
| `canmate` | `side:w/b`, `canMate:boolean`; currently a material heuristic with a known defect |

`capturedDropType` is `p`, `n`, `b`, `r`, `q`, or null. A captured promoted piece
reports `p`. In bughouse the host routes that piece to the partner board; the
engine does not add it to either reserve on the current board.

Example, the complete response to `apply e2e4 startpos`:

```json
{"ok":true,"legal":true,"fen":"rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1","sideToMove":"b","inCheck":false,"terminal":"none","capturedDropType":null}
```

`getfen` reports effective draw behavior. For standard chess it reports
`drawRules:"standard"` even when the option is at its default `variant` value,
because standard chess enables these checks under its variant defaults.
JSON key order and move-list order should not be used as API guarantees.

## Errors and process failure

```text
apply z9z9 startpos
```

```json
{"ok":false,"error":"malformed_request","reason":"unparseable move 'z9z9'"}
```

```text
apply e2e5 startpos
```

```json
{"ok":false,"error":"illegal_move","reason":"not legal in this position"}
```

| Signal | Meaning / host behavior |
|---|---|
| `malformed_request` | Invalid inline position, move syntax, side, or required argument. Reject the request; do not treat the reply as a position update. |
| `illegal_move` | Parsed move is not legal in the supplied position. Reject it. |
| `internal_error` | Reserved code; no current emission path. |
| EOF, nonzero exit, timeout, malformed response | Process/protocol failure. Discard the result and replace the worker as appropriate. |

The taxonomy does not turn every UCI setup error into JSON. Consume health and
setup text separately. Bound client-side waits; a faulting process may be unable
to emit a reply. Unknown commands can produce no reply.

## Terminal status and adjudication limits

`terminal` can be `none`, `checkmate`, `stalemate`, `draw_fifty_move`,
`draw_threefold`, or `draw_insufficient_material`. No-legal-move outcomes are
checked first. `repetitions` counts prior occurrences in the supplied history;
threefold is two prior occurrences. A lone FEN carries no repetition history.

The current API automatically labels fifty-move/threefold cases when its checks
are enabled; it does not encode a host's claim workflow or a complete FIDE
fivefold/75-move/dead-position policy. `canmate` is not a mate search and does not
currently implement complete possible-mate adjudication. The material heuristic
can even return a draw for a mate-in-one position; see
[the reproducible limitation](limitations.md#material-adjudication).

`apply` checks move legality, not whether a host has already declared the game
over. It can apply a legal move after a draw status. The host must enforce its
own game lifecycle and must not use the defective material status as an
unconditional adjudication authority.

## Host-managed bughouse

Select `UCI_Variant=bughouse` before supplying a bracketed reserve FEN. Captures
return `capturedDropType` without replenishing a reserve here. Persist `~`
promoted markers and route captures to the teammate on the other board. Inject
updated hands through subsequent FENs. A server must define its own cross-board
ordering, clocks, sitting, and partner policy.

`DrawRules=variant` disables repetition/fifty-move draws on a bughouse board;
`DrawRules=standard` enables those per-board checks. Neither policy repairs
material adjudication. See [variants](variants.md).

## Versioning and health

`uci` advertises the variant options; `isready` replies `readyok`. The custom
JSON surface currently has no schema-version negotiation. Pin and test the
engine version your adapter consumes. Do not infer support for a command merely
because an unrelated command succeeds. [Stability](stability.md) distinguishes
this extension from internal engine details.
