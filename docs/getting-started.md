# Getting started

## Download and select an executable

Download from the [releases](https://github.com/fcmv/Vector-64/releases).
Choose the operating system and CPU profile first, then a capability suffix.

| Profile | Requirement |
|---|---|
| Linux `x86-64-v2` | x86-64-v2 baseline, including SSE4.2 and POPCNT. |
| Linux `x86-64-v3` | x86-64-v3 baseline, including AVX2 and BMI2. |
| Windows `x86-64-avx2` | An AVX2-capable x86-64 CPU. |
| Linux `arm64` | Baseline ARM64 build. |
| Linux `arm64-dotprod` | ARMv8.2 with dot-product instructions. |
| macOS `arm64` | Apple Silicon. |

Select `-nnue` for standard chess with the embedded network, `-all` for standard
chess plus drop variants, or `-viz` for the visualizer. `-validator` refuses
search and is intended for integration workers. The unsuffixed binary uses
classical evaluation until an external network is loaded. The README has the
complete [binary table](https://github.com/fcmv/Vector-64#choose-a-binary).

The release currently distributes bare executables. On Unix, make the file
executable with `chmod +x <downloaded-file>`. If your CPU is unsupported, build
from source with appropriate compiler flags; `ENGINE_NATIVE=OFF` does not remove
MSVC's AVX2 requirement. Linux runtime/library compatibility also depends on the
release's build environment, not just its CPU suffix.

## Connect a chess GUI

In a GUI that supports UCI, add a new engine and select the executable. Use the
GUI's engine-options dialog to set `Threads`, `Hash`, and optional tablebase or
network paths. Let the GUI manage positions, clocks, and game boundaries.

The engine does not display a board in ordinary UCI mode. Its stdin/stdout
connection is the interface. For a board and neural telemetry without a
separate chess GUI, run `ChessEngine-viz`; it opens a local browser page.

## Run an interactive session

For a single-configuration source build:

```bash
./build/bin/ChessEngine-nnue
```

For an MSVC Release build:

```powershell
.\build\bin\Release\ChessEngine-nnue.exe
```

Send `uci` and wait for `uciok`. The intervening `option` lines advertise the
capabilities of that binary. Send `isready` and wait for `readyok`. Then enter:

```text
setoption name Threads value 1
setoption name Hash value 64
ucinewgame
position startpos moves e2e4 e7e5
go depth 6
```

The engine emits `info` lines and eventually `bestmove <move>`, possibly with a
ponder move. Only then send `quit`. Sending all commands, including `quit`, in
one unpaced pipe can interrupt the asynchronous search.

For a complete runnable client that waits for replies:

```bash
python examples/uci_client.py --engine build/bin/ChessEngine-nnue --depth 6
```

On MSVC replace the engine path with
`build/bin/Release/ChessEngine-nnue.exe`; on MSYS2 use
`build/bin/ChessEngine-nnue.exe`. The client needs only Python's standard library.

## Inspect a position

`eval` reports a static score from the side to move's perspective; positive
favors that side. Search `info` scores are also side relative, with `score mate`
used for mate-distance reports. A score is an engine estimate, not a calibrated
winning probability or a playing-strength rating.

Use the [validator](validator.md) to enumerate legal moves or read a FEN back.
Use [perft](testing.md#perft-and-divide) for move-generation diagnostics.

## Load a network or tablebases

```text
setoption name EvalFile value /absolute/path/candidate.nnue
setoption name SyzygyPath value /absolute/path/tablebases
isready
```

Use a 1024-wide STK-HalfKA file with `EvalFile`, or a 128-wide file with
`EvalFileSmall`. The default `-nnue` and `-all` binaries already contain the big
network. The engine accepts its own format, not arbitrary Stockfish `.nnue`
files. Validate an external file before use:

```bash
python tools/nnue/check_vector64.py artifacts/candidate.nnue
```

Syzygy data is not included. Point `SyzygyPath` at your `.rtbw` / `.rtbz` files.
The engine reports whether usable tables were found. Keep the option empty for
drop-variant search: the current probing path lacks a runtime-variant guard.
See [Syzygy integration](syzygy.md) for coverage and other restrictions.

See [known limitations](limitations.md) before using the validator for game
adjudication or replacing a network in a long-lived process.
