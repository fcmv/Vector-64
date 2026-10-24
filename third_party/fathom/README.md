# Vendored Fathom and Syzygy integration

The probing sources are vendored from [Fathom](https://github.com/jdart1/Fathom)
at commit `c9c6fef0dddc05d2e242c183acf5833149ab676d`, under the
[MIT license](LICENSE): `tbprobe.c`, `tbprobe.h`, `tbchess.c`, `tbconfig.h`,
and `stdendian.h`. Keep upstream attribution with redistributed copies.
Tablebase data files are separate and are not included in this repository.

## Use tablebases

Set the UCI option while the engine is idle, then wait for readiness:

```text
setoption name SyzygyPath value /absolute/path/tablebases
isready
```

Supply `.rtbw` files for WDL coverage and `.rtbz` files for DTZ coverage. Fathom
supports directory lists separated by `;` on Windows and `:` on Unix. An empty
path or `<empty>` clears the loaded set. The engine reports whether tables were
found; `readyok` alone does not establish coverage of a particular position.

These are standard-chess tables. Root and interior probing are disabled for
crazyhouse and bughouse on every search worker. Switching `UCI_Variant` does
not unload the files; returning to standard chess can use them again.

## Search behavior

The wrapper is `src/search/syzygy.{h,cpp}`. Keep engine-side calls behind that
wrapper; Fathom owns process-global tablebase state. Loading another path frees
the previous set, so hosts should configure each worker while idle.

Interior WDL probing requires a non-root node, no excluded singular-verification
move, a zero halfmove counter, no castling rights, and a piece count within the
loaded coverage. A missing/unsupported probe falls back to normal search.
The wrapper maps cursed wins and blessed losses to draw and ordinary wins/losses
to internal scores of +/-800000, below the mate band.

At the root, the master thread tries DTZ ranking with the current halfmove
counter and fifty-move handling. It falls back to WDL ranking when DTZ ranking
fails. The wrapper passes whether any position repeated since the last capture
or pawn move, including an earlier cycle when the current root has not repeated.
Fathom then prefers DTZ progress after repetition. FEN input alone has no prior
position history; use `position ... moves ...` to preserve it. Root probing is
master-only; interior WDL calls are the thread-safe path.

Root tablebase ranking considers only the caller's legal candidates after
`searchmoves` filtering. Every equally best-ranked allowed move remains for
normal search, even if that restricted set excludes every globally optimal
move. Probe failure leaves the candidate list unchanged. WDL fallback preserves
the same restriction but lacks DTZ progress guidance.

## Build and maintenance

`CMakeLists.txt` compiles `tbprobe.c` as C++. Fathom then selects `std::atomic`
and `std::mutex`, avoiding dependence on MSVC's opt-in C11 `<stdatomic.h>` path.
Supported toolchains are described in [building](../../docs/building.md); this
configuration is not a guarantee for every C++ toolchain.

Vendored files are excluded from the repository's formatting checks, and the
local `.clang-tidy` disables checks for them. Keep upstream updates separate
from adapter changes and record the new source revision when refreshing them.

For a change to probing, run the normal [engine checks](../../docs/testing.md)
and an endgame search with identified table files, expected WDL/DTZ behavior,
clock state and missing-file fallback. A build without external table data does
not verify actual probing coverage.

`search.syzygy_adapter` checks root restrictions, underpromotion identity,
repetition propagation and DTZ-to-WDL/failure handling without external files.
To register `search.syzygy_tables` against real three-piece WDL and DTZ files:

```bash
cmake -S . -B build -DSTK_SYZYGY_TEST_PATH=/absolute/path/three-piece-tables
cmake --build build -j
ctest --test-dir build -R search.syzygy --output-on-failure
```

The real-file test covers all singleton root restrictions in a KQvK position,
one- and two-thread searches, the fifty-move boundary, and progress selection
after an earlier repetition. Keep table files and their provenance separately;
they are not fetched during configure or included in the repository.
