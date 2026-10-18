# Variants

Runtime variants are `chess`, `crazyhouse`, and `bughouse`. Select them with
`setoption name UCI_Variant value ...` in a variant-capable binary. Chess960,
atomic, horde, four-player chess, and other geometries are not implemented
runtime choices.

## Binary and evaluation boundaries

`ChessEngine-all` embeds the standard-chess NNUE and supports all three choices.
`ChessEngine-variants` supports the same rules without an embedded net.
`ChessEngine-validator` exposes rule queries and refuses search. The ordinary
`ChessEngine` and `ChessEngine-nnue` targets do not contain variant state.

Drop variants automatically use classical evaluation, even with a standard
network loaded. The current STK-HalfKA network has no reserve features or drop
accumulator path. Its feature set and topology remain the current architecture;
a different variant network is not part of this documentation update. Returning
to `chess` restores the loaded standard network.

Keep `SyzygyPath` empty for drop-variant search. The tablebase data describes
standard chess, but the current search lacks a runtime-variant probing guard.
Changing `UCI_Variant` does not unload tables. See
[tablebase limitations](limitations.md#tablebase-search).

## Drops and reserves

A drop places a reserve piece on an empty square. Pawns cannot be dropped on
ranks 1 or 8; kings cannot be held or dropped. Existing pawns on a file do not
prevent another pawn drop. A checking drop and drop-mate are allowed by this
rules implementation. UCI notation uses an uppercase piece letter regardless
of mover: `P@e4`, `N@f7`.

A drop cannot remove a blocker shielding its own king. When in single slider
check, it may block between king and checker. Knight/pawn checks and double
checks cannot be answered by a drop. The generator and legal filter enforce
these conditions.

| Behavior | Crazyhouse | Bughouse board |
|---|---|---|
| A local capture | Adds the reverted captured type to the capturer's reserve. | Adds nothing to either local reserve; the host transfers it to the partner board. |
| A drop | Spends from the mover's reserve. | Spends from the host-supplied mover's reserve. |
| Partner board / sitting | Not applicable. | Not implemented by this engine. |
| Default repetition/fifty-move checks | Enabled. | Disabled. |
| Neural evaluation | Suppressed. | Suppressed. |

A promoted piece captured in either drop variant becomes a pawn for transfer.
The `capturedDropType` reply already performs this reversion.

## FEN and persistence

The board field carries reserves in brackets and promoted pieces with `~`:

```text
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1
```

Uppercase reserve letters belong to White, lowercase to Black: `[QPpp]` means
White has a queen/pawn and Black has two pawns. Empty reserve is `[]`.
A promoted queen is written `Q~` in the board field. Persist this marker:
without it, a later capture cannot know that the piece must revert to a pawn.
The standard parser rejects bracketed variant FEN rather than discarding hands.

A host should persist the FEN emitted after `apply`, plus the move history
needed by its repetition policy. Replacing a board with a new FEN does not
preserve earlier occurrences automatically. Reserves and promoted markers
participate in the variant hash.

## Worked crazyhouse capture

```text
setoption name UCI_Variant value crazyhouse
position startpos moves e2e4 d7d5 e4d5
apply d8d5
```

```json
{"ok":true,"legal":true,"fen":"rnb1kbnr/ppp1pppp/8/3q4/8/8/PPPP1PPP/RNBQKBNR[Pp] w KQkq - 0 3","sideToMove":"w","inCheck":false,"terminal":"none","capturedDropType":"p"}
```

White's pawn captured on d5 supplied White's reserve. Black's queen then
captured that pawn and supplied Black's reserve. In bughouse neither capture
would add to the current board's reserve; the server would route each transfer.

## Draw profile and game lifecycle

`DrawRules=variant` uses the defaults above. `DrawRules=standard` forces the
implemented repetition/fifty-move checks on, including for bughouse boards.
Stalemate and the current material predicate are still reported in either
bughouse setting. These per-board statuses are not a complete cross-board
bughouse game result.

The [validator limitations](validator.md#terminal-status-and-adjudication-limits)
apply to all rule profiles. Legality queries are separate from the host's game
termination, flag adjudication, and claim policy.

## Search and measured defaults

The classical variant evaluation accounts for board material/PSQT, reserve
material, adjusted variant piece values, and reserve-related king danger.
Drop history has its own ordering table. Null-move pruning remains enabled by
default. Checking drops can be generated in quiescence under a compile-time
experiment switch, but its default depth is zero after the reported self-play
experiments. Do not describe that disabled path as a missing generator.

| CMake variable | Default | Purpose |
|---|---|---|
| `ENGINE_DROP_CHECK_QDEPTH` | `0` | Checking-drop quiescence depth. |
| `ENGINE_VARIANT_HAND_MATERIAL` | `1` | Include reserve material. |
| `ENGINE_HAND_VALUES` | empty | Override reserve piece values; empty uses board `PieceValue`. |
| `ENGINE_KING_DANGER_SCALE` | `6` | Reserve-related king-danger weight in eighths. |
| `ENGINE_PIECE_VALUES` | `0,100,340,320,450,800,0` | Variant board-value correction. |
| `ENGINE_VARIANT_NULLMOVE` | `1` | Permit null-move pruning in drop variants. |
| `ENGINE_VARIANT_DROP_HISTORY` | `1` | Dedicated drop history. |

The SEE model does not fully account for material entering reserves. The
no-reserve bughouse path is not representative of partner-fed play. A standalone
bughouse match from start position receives no partner pieces and therefore
cannot measure real drop strength. See [benchmark methodology](benchmark.md)
for experiment requirements; this page does not assign an absolute Elo rating.

Historical [variant experiment notes](experiments/variant-search.md) retain the
reported W/D/L and tuning comparisons, with their provenance limitations.

## Verification

`variants.drops_state_and_perft` checks reserve/promoted/hash state, legal/drop
move generation, make/unmake, and the crazyhouse start-position perft anchors.
Depths 1-4 match standard chess; depth 5 is 4,888,832 instead of 4,865,609.
The standard and variant cores are compiled separately to avoid runtime variant
branches in the standard engine. A semantics-preserving variant change should
preserve standard search signatures; deliberate search changes need their own
justification and regenerated baselines.
