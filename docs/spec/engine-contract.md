# Engine contract

This reference describes current checkout behavior. The UCI and validator pages
are the protocol references; the STK-HalfKA page owns the network contract.
Known deviations are explicit in [limitations](../limitations.md). The current
NNUE feature set and topology are fixed for this documentation work.

## Representations

Squares use little-endian rank-file indexing: a1 is 0 and h8 is 63. A bitboard
is an unsigned 64-bit mask. White is color 0 and Black color 1. Piece types run
from pawn through king with a no-piece sentinel.

`Move` packs `from | (to << 6) | (flag << 12)` into 16 bits. Zero is the none
sentinel. Flags distinguish double pushes, captures, castling, en passant, and
promotion type. Variant drops use flag 5 and encode a piece type in the source
field. Standard move lists have 256 entries; variant builds have 512. Capacity
checks in `push_back` are assertions, not a general external-input safety proof.

Position state consists of board occupancy, mailbox, mover, castling/en-passant
state, halfmove/fullmove counters, Zobrist identity, repetition history, and
incremental evaluation totals. Variant reserves and promoted markers participate
in their position identity. Clocks are serialized in FEN but are not substitutes
for supplied move history.

## Input and legality

UCI positions accept `startpos` or FEN followed by optional UCI moves. The UCI
boundary rejects a position where the side not to move is in check, and replays
supplied moves against legal generation. It accepts four-field FEN forms in
some paths; examples use all six fields to make clocks explicit.

This is not a reachability proof from the initial position. A syntactically
accepted setup is not evidence that every historical sequence leading to it
was legal. Training's lightweight FEN decoder performs encoding checks rather
than full engine legality validation.

For standard chess, legal generation covers castling, en passant and all four
promotion choices. UCI castling uses king coordinates (`e1g1`, `e1c1`), not
Chess960 rook-square notation. Chess960 is not a supported runtime variant.

Drop syntax, reserve ownership, promoted-piece reversion, and rule profiles are
specified in [variants](../variants.md). Bughouse represents one board with
external partner transfers.

## Make/unmake and identity

Every legal transition updates board state, clocks, castling/en-passant state,
material/PSQT and hash. Unmake restores the prior state. A history-bearing
`position ... moves ...` request makes repetition visible; loading only the
last FEN loses that history.

Search's internal repetition convention uses a previous occurrence to avoid
cycles. The validator exposes the number of prior occurrences within its
fifty-move window; `repetitions >= 2` triggers its threefold status. An
independent host's claim/automatic-draw policy must account for this distinction.

The terminal validator checks no-legal-move outcomes first, then its material
predicate, then fifty-move and threefold conditions. Its material predicate is
known to misclassify positions. Fivefold repetition, 75-move automatic draws,
and general dead-position reachability are not a complete implemented FIDE
adjudication contract.

## Evaluation and search

Classical board evaluation maintains White-minus-Black material and PSQT, then
applies the mover sign. STK-HalfKA directly emits a mover-relative integer score
with its own PSQT side output. No additional classical PSQT blend is applied to
that network result. Search can select a lazy classical estimate or optional
small net under documented gates.

`score cp` is a centipawn estimate; `score mate` is signed full moves to mate.
Positive favors the root side to move. Internal mate constants and TT mate-ply
normalization are implementation details, not portable score units for clients.

Standard search is iterative-deepening alpha-beta with quiescence and selective
pruning. A returned move is an engine choice, not an optimal-play guarantee.
Search decisions, PVs, scores, and fingerprints may change with deliberate
search or network changes. A multi-threaded or wall-clock-limited run is not
promised reproducible.

## Lifetime and failures

One process owns one resident position and its search state. A host should
serialize requests to that process or use a process pool. Search runs
asynchronously; stdin EOF and `quit` shut down the worker. UCI readiness,
search completion, and a successful position parse are distinct events.

Inline validator queries leave resident state unchanged. Two-line setup/query
requests depend on state retained between lines, including after a rejected
setup. Malformed inline positions receive structured errors; malformed UCI
setup prints text. Engine crashes, EOF, and timeouts are process failures;
`internal_error` is a reserved extension code and is not currently emitted.

Network loading checks its header and reads the defined payload. It currently
uses host-native integer reads and permits trailing data; the Python checker
expects the little-endian exact-size contract unless explicitly told otherwise.
Supported build targets are little-endian. A failed payload read can corrupt a
loaded network, so callers must not continue using that process after a failed
replacement.

See [stability](../stability.md) for compatibility boundaries and
[testing](../testing.md) for executable checks and their limits.
