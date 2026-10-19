# Vector Scope

Vector Scope renders the existing STK-HalfKA forward pass while the engine plays
or analyzes positions. The native binary embeds the default big network and the
committed UI. Telemetry is a separate capture outside search's hot path; tests
compare its integer values and layer contributions against the evaluator.

## Run the native viewer

```bash
./build/bin/ChessEngine-viz
./build/bin/ChessEngine-viz --port 8080 --nodes 50000 --threads 4
./build/bin/ChessEngine-viz --headless
./build/bin/ChessEngine-viz --terminal
```

MSVC paths include `bin/Release/` and Windows names end in `.exe`. Native HTTP
binds loopback, port 7777 by default. `--headless` suppresses browser opening;
`--terminal` runs the plain-text live view. Stop the process with your terminal's
interrupt command. `--help` lists the executable's flags:

| Flag | Default / purpose |
|---|---|
| `--port` | 7777, local HTTP port. |
| `--net` | Load this file, otherwise use embedded big net; a failed explicit load can fall back to the embedded net. |
| `--net-b` | Optional comparison net. |
| `--nodes` | 20000 per move. |
| `--threads` | 1 search thread. |
| `--hash` | 32 MB. |
| `--delay` | 300 ms between self-play moves. |
| `--seed` | Opening seed. |
| `--record` | Write frame summaries to JSONL, replacing an existing file. |
| `--no-browser`, `--headless` | Serve without opening the browser. |
| `--terminal` | Console view instead of HTTP. |

## Modes and reading the field

Self-play creates games; analysis accepts a FEN; play mode lets a human choose
moves supplied by the engine; datagen records labelled positions. The net
inspector shows transformer/dense statistics and the king-bucket map. The API
mode values are `selfplay`, `analysis`, `human`, and `datagen`.

```text
active features -> two H=1024 accumulators -> pairwise clipped activation
                -> concatenated H=1024 vector -> L1=16 -> L2=32 -> output
```

The displayed value includes the network's PSQT side output. Accumulator colors
represent signed values; clipped layers use the 0..127 activation range. Edges
show selected large `weight * activation` contributions, not every connection.
During search the view can follow the PV leaf rather than the root. A captured
forward pass is an exact evaluation of that sampled position, not a record of
every visited search node or an explanation of why search selected a move.

## Native transport and controls

| Endpoint | Reply / behavior |
|---|---|
| `GET /` | Embedded single-file UI, or a placeholder when built without it. |
| `GET /api/health` | JSON liveness reply. |
| `GET /api/state?since=N` | Framed state; waits for a newer sequence or the five-second wait timeout. |
| `GET /api/net` | Network-inspector JSON. |
| `POST /api/control` | JSON object with `cmd` and arguments; success is `{"ok":true}`. |

State framing is `[uint32 LE header length][UTF-8 JSON header][raw LE buffers]`.
The header describes names, element types, lengths, game/search state, architecture,
and auxiliary recording/datagen state. Clients request sequentially, giving
backpressure. A timeout can return a snapshot without a newer sequence; clients
must inspect `seq` rather than assuming every reply advances it.

| `cmd` | Arguments / effect |
|---|---|
| `pause`, `step`, `newgame` | Boolean `value` for pause; advance or reset game. |
| `nodes`, `threads`, `depth`, `delay`, `variety` | Integer `value`; adjust session search/pacing. |
| `mode` | String `value`: selfplay, analysis, human, datagen. |
| `position` | `fen` plus optional `moves` array. |
| `move` | UCI move in string `value`. |
| `enginecolor` | Integer color in `value` (White 0, Black 1). |
| `randomopening` | Boolean `value`. |
| `comparenet` | File path in string `value`. |
| `record` | File path in `value`; empty stops recording. |
| `datagen` | `action`: start, stop, probe. Start accepts output/targets/search/shard/seed settings and optional resume. |

Most controls are locked during datagen to preserve row-shaping settings; pause
and datagen actions remain available. The C++ handler in `src/viz/wire.cpp` is
the complete argument contract; UI controls can expose a smaller set. Invalid
controls return an error JSON/HTTP status, not a UCI reply.

The server caps request payloads at 64 KiB and read/write timeouts at ten seconds.
It is unauthenticated and local. Embedded web assets do not imply no filesystem
access: network comparison reads files and recording/datagen writes files with
the process's permissions. Do not expose the server publicly as a hosted service.

## Build and edit the UI

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENGINE_NATIVE=OFF
cmake --build build --target ChessEngine-viz -j
```

A C++ build needs no Node: `ui/dist/index.html` is committed. To modify the UI,
use Node 24, matching CI:

```bash
cd ui
npm ci
npm run typecheck
npm run dev
```

Run the native viewer separately; Vite on port 5173 proxies `/api` to native port
7777. The UI probes same-origin `/api/health`; it does not scan localhost ports.
When finished, run `npm run build` and commit the regenerated HTML with its
sources. CMake declares the net/bundle embedding dependencies so changes rebuild.
`ENGINE_VIZ=OFF` removes all native visualization targets and tests.

## Browser engine

```bash
source /path/to/emsdk/emsdk_env.sh
bash tools/build_wasm.sh
python -m http.server -d ui/dist-wasm 8080
```

Open `http://localhost:8080`. The build copies the page, service-worker shim,
module, wasm and default net into the deployable directory. Keep all generated
runtime files together. The net is fetched and cached through Cache Storage;
use versioned URLs or clear the cache when replacing a file at the same path.

The pthread build requires SharedArrayBuffer and cross-origin isolation. The
MIT service-worker shim supplies isolation headers on suitable static hosts;
registration requires a secure context (localhost or HTTPS). When isolation is
unavailable, startup explains the failure and offers reload; there is no
single-thread fallback. Native transport does not require this isolation.

The same C++ telemetry encoder serves HTTP and WASM, but the WASM source list is
maintained explicitly in `tools/build_wasm.sh`. Portable scalar NNUE is compiled
with `-msimd128`; no separate handwritten WASM integer kernel is claimed. CI
currently checks the generated files, not a complete browser/runtime parity run.

## Walkthroughs and detailed contracts

The [illustrated tour](visualizer-tour.md) explains actual screenshots and
live recordings. [Telemetry and controls](spec/telemetry.md) specifies fields,
buffer layout, errors and recording semantics. [Data generation](datagen.md)
covers row labels and resume; [browser deployment](browser-deployment.md)
covers hosting, isolation and cache updates.

## Verification

Run `ctest --test-dir build -R viz --output-on-failure` plus the native
`tools/viz_smoke.sh` check. Build a C++ fixture and pass its absolute path as
`VIZ_FIXTURE` to `npm test` for the decoder contract. See [testing](testing.md).
Search fingerprints come from `tools/bench_signature.txt`; do not duplicate
changing count values here. UI/license terms are in [component notices](third-party-notices.md).
