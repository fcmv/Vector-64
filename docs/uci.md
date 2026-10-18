# UCI reference

The executable reads one command per line from stdin and flushes each output
line to stdout. An ordinary engine starts in UCI mode. Search is asynchronous;
clients must read replies while sending commands. Source: `src/uci/uci.cpp`.

## Connection and lifetime

1. Send `uci`; read identity/options through `uciok`.
2. Set options, send `isready`, and wait for `readyok`.
3. Before a new game, send `ucinewgame` and the desired position.
4. Send `go` with a budget; read `info` through `bestmove`.
5. Use `stop` to end an active search and wait for its final `bestmove`.
6. Send `quit` to close the process. EOF also shuts it down.

`isready` is a responsiveness probe, not a search-completion barrier or a
position-parse acknowledgement. Reuse a process for serialized requests; do not
multiplex independent games through its resident state.

## Options

Defaults are startup values. `Threads` is hardware-dependent on search binaries;
validator-only startup uses one thread and a 1 MB hash. Query your own binary's
`uci` output instead of assuming a machine's detected thread count.

| Name | Type | Default | Advertised range / values | Meaning |
|---|---|---|---|---|
| `Threads` | spin | hardware concurrency; validator 1 | 1..64 | Search workers; set explicitly for reproducible tests. |
| `Hash` | spin | 8; validator 1 | 1..4096 MB | TT allocation; resizing discards its contents. |
| `Move Overhead` | spin | 30 | 0..500 ms | Reserve from time budgets for communication/overhead. |
| `Ponder` | check | false | true/false | Advisory option; pondering is driven by `go ponder`. |
| `EvalFile` | string | `<empty>` | STK-HalfKA H=1024 path | Load/replace the big network; an embedded net may already be active. |
| `EvalFileSmall` | string | `<empty>` | STK-HalfKA H=128 path | Load the optional small network. |
| `SyzygyPath` | string | `<empty>` | Tablebase path | Load tablebases; an empty value clears them. |
| `SmallNetThreshold` | spin | 950 | 0..5000 cp | Use the loaded small net at large classical-estimate magnitudes during big-net search. |
| `LazyEvalMargin` | spin | 0 | 0..5000 cp | Nonzero permits a classical estimate instead of a network forward beyond this magnitude. |
| `ShowStats` | check | false | true/false | Additional search diagnostics. |
| `PersistOrdering` | check | true | true/false | Retain ordering history across searches within a game. |
| `MultiPV` | spin | 1 | 1..32 | Number of root principal variations. |
| `UCI_Variant` | combo | chess | chess, crazyhouse, bughouse | Variant builds only; switching resets position/search state. `standard` is also accepted as a chess alias. |
| `DrawRules` | combo | variant | variant, standard | Variant builds only; choose variant defaults or force standard repetition/fifty-move checks. |
| `SearchJson` | check | false | true/false | Variant builds only; emit a JSON summary after `bestmove`. |

Changing allocation, network, tablebase, thread, and variant options stops active
search before applying the change. Set options while idle. Empty `EvalFile` and
`EvalFileSmall` are ignored; they do not unload a network. There is no advertised
`Clear Hash` option: `ucinewgame` clears search state. Unknown commands/options
can be ignored, so their silence is not a capability acknowledgement.

## Positions and moves

```text
position startpos
position startpos moves e2e4 e7e5 g1f3
position fen 7k/8/8/8/8/8/8/K5R1 w - - 0 1
```

Moves use long UCI coordinates with a promotion suffix (`e7e8q`). Castling is
encoded as a king move (`e1g1`). Drops in a variant-capable binary use `P@e4` or
`N@f7`; select the variant before supplying its FEN/moves.

FEN examples use all six fields. A rejected FEN or illegal move list prints an
`info string` and preserves the previous position. A later query can therefore
succeed against old state. Hosts needing one structured failure per request
should use [inline validator requests](validator.md#self-contained-requests).

## Search limits

| Form | Meaning |
|---|---|
| `go depth 6` | Iterative search to the requested nominal depth, subject to other limits. |
| `go nodes 50000` | Node-limited search; stopping checks occur periodically, so a budget is not an exact output node count. |
| `go movetime 1000` | Fixed wall-clock allocation in milliseconds. |
| `go wtime 60000 btime 60000 winc 1000 binc 1000` | Clock-driven allocation with increments. |
| `go ... movestogo 30` | Include a moves-to-control estimate. |
| `go infinite` | Search until stopped or implementation depth limits are reached. |
| `go depth 6 searchmoves e2e4 d2d4` | Restrict legal root candidates; clear `SyzygyPath` because current root tablebase ranking can replace that restriction. |
| `go ponder ...` | Ponder until `ponderhit` starts the budget clock or `stop` ends it. |

Wait for `bestmove` before quitting. A no-legal-move result uses `bestmove 0000`.
`ChessEngine-validator` and validator-only mode refuse `go` and `bench` with a
text diagnostic, rather than a JSON search response.

## Output conventions

`info` lines report completed iterations, nodes, elapsed time, depth, score and
PV. A positive `score cp` favors the root side to move; `score mate` uses signed
full moves. `multipv` lines identify separate root variations. Human diagnostic
wording is not a stable machine-readable schema.

With `SearchJson=true`, the normal UCI `bestmove` is followed by a JSON object
with `bestMove`, `score`, `pv`, and `depth`. `score` contains `cp` or `mate`.
An optional `ponder` field can also be present. Keep consuming lines after
`bestmove` when using this extension. The summary describes the recorded search
iteration; a search stopped before completing an iteration may have sparse or
zero-depth data.

## Diagnostics and tablebases

`eval` prints a static evaluation. It prefers the big net, then a small net
when only that one is loaded, then classical evaluation. It is not a simulation
of every search lazy/dual-net selection gate.

`bench [depth]` is synchronous and runs a fixed position suite. The
[signature checker](testing.md#search-fingerprints) supplies its canonical
threads/hash settings and reads the expected count from the central file.

Set `SyzygyPath` to a directory or supported path list containing external
`.rtbw`/`.rtbz` data. Fathom restricts probes to positions its tables cover;
positions with castling rights cannot be probed. Interior WDL calls also require
a zero halfmove counter. The wrapper treats cursed wins and blessed losses as
draws under its fifty-move interpretation. Root DTZ ranking is master-only and
falls back to WDL ranking; its repetition flag is currently hard-coded false.

Keep `SyzygyPath` empty for drop-variant search. Tables are standard-chess data,
and the current search lacks an explicit variant guard. Switching variants does
not unload them. Root tablebase ranking can also replace a `searchmoves`
restriction. See [Syzygy integration](syzygy.md) and
[known limitations](limitations.md#tablebase-search).

## Reproducibility

Record the executable/source revision, net hash, all options, position/history,
budget, and reset sequence. Compare fresh or equivalently cleared processes,
`Threads=1`, and fixed node/depth budgets. Warm ordering/TT state, time limits,
SMP scheduling, or deliberate search changes can alter the PV and best move.
Scalar/SIMD integer inference equality does not imply identical wall-clock-limited
search results.
