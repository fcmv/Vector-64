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

These are standard-chess tables. Keep `SyzygyPath` empty in a process doing
crazyhouse or bughouse search: the current engine does not explicitly guard
its probing path by runtime variant. Switching `UCI_Variant` does not clear
loaded tables. See [the documented limitation](../../LIMITATIONS.md#tablebase-search).

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
fails. The wrapper supplies `hasRepeated=false`; it does not pass the actual
repetition history to that DTZ call. All equally best-ranked legal moves remain
for normal search. Root probing is master-only; interior WDL calls are the
thread-safe path.

Root tablebase ranking currently replaces the root candidate list after
`searchmoves` filtering. Do not combine a required root restriction with loaded
tables until that interaction is fixed. Clear `SyzygyPath` for such a request.

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
