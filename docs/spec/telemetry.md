# Vector Scope telemetry and controls

This reference follows `src/viz/wire.cpp`, `server.cpp` and
`ui/src/engine/{types,decode}.ts`. Native HTTP and WASM use the same encoder.
It is a local visualization interface, separate from UCI/validator JSON. There
is no negotiated schema version or request multiplexing contract; pin a build
and verify its C++/TypeScript fixture before writing another client.

## HTTP surface

| Method/path | Response |
|---|---|
| `GET /` | Embedded HTML. |
| `GET /api/health` | `application/json`, `{"ok":true}`. Liveness only. |
| `GET /api/state?since=N` | `application/octet-stream`, one framed state; `Cache-Control: no-store`. |
| `GET /api/net` | JSON architecture and network-inspector statistics. |
| `POST /api/control` | JSON request; success 200 `{"ok":true}` or probe data; rejected controls 400 `{"ok":false,"error":"..."}`. |

State long-polls for `seq > since` or five seconds. Timeout can return the
current snapshot with the same sequence. Invalid `since` falls back to zero.
Keep one poll outstanding, render/decode it, then request the next sequence.
This provides backpressure, not a lossless history of every visited position.
Read/write timeouts are ten seconds and payloads are capped at 64 KiB.

## Binary framing

```text
byte 0..3                uint32 little-endian JSON header byte length H
byte 4..(4+H-1)          UTF-8 JSON
byte (4+H)..end          concatenated raw little-endian arrays
```

Walk `header.frame.buffers` in order. Each entry has `name`, `type` and `len`;
`len` counts elements. Types are `u8` (1 byte), `i16` (2) and `i32` (4).
There is no alignment padding or explicit offset field. Copy/decode arrays
rather than assuming aligned typed-array views into the original frame.
The current TypeScript decoder uses native-endian typed arrays; an independent
portable decoder should explicitly decode little-endian multi-byte elements.
Validate lengths/bounds before allocating or reading untrusted frames.

| Buffer | Type/shape for H=1024 | Interpretation |
|---|---|---|
| `accUs`, `accThem` | i16[1024] each | Signed accumulators, sampled mover/opponent order. |
| `l1in` | u8[1024] | Pairwise-clipped, concatenated layer input. |
| `l1out`, `l2out` | u8[16], u8[32] | Clipped activations. |
| `outContrib` | i32[32] | Output weight-times-activation terms. |
| `l2Contrib` | i32[32 * 16] | L2 target-major contributions from L1. |
| `l1Top` | i32[16 * K * 2] | Target-major `(source index, contribution)` pairs; K is `frame.l1TopK`. |
| `whiteFeatures`, `blackFeatures` | i32[feature count * 6] | `(square, orientedSquare, pieceColor, pieceType, pieceKind, featureIndex)`. |

Use the transmitted architecture and lengths, not this table as hard-coded
offsets. `nnueActive=false` means no usable neural frame; the UI exposes
`frame=null`. Colors are 0 White/1 Black, squares a1=0 and types pawn=1..king=6.
Feature orientation and bucket arithmetic follow [STK-HalfKA](../vector64-spec.md).

## JSON header groups

| Group | Fields and interpretation |
|---|---|
| Session | `seq`, `mode`, `running`, `paused`, `thinking`, `nnueActive`, `threads`, `varietyCp`, `hardwareThreads`, `maxDepth`, `engineColor`. |
| `arch` | `hidden`, `pair`, `l1`, `l2`, `psqtBuckets`, `kingBuckets`, `pieceKinds`, `features`, `actMax`. |
| `game` | `fen`, `startFen`, `moves`, `lastMove`, `ply`, `over`, `result`, `reason`, `gameIndex`, White `wins/draws/losses`, `whiteMs`, `blackMs`, `clockRunning`. |
| `search` | `depth`, `seldepth`, `scoreCp`, `nodes`, `tbHits`, `elapsedMs`, `nps`, `pv`, `qsearchTtHitRate`, `negamaxTtHitRate`. |
| Root lists | Top-level `candidates`: `move`, `scoreCp`, `pv`; `legalMoves` for current human-play requests. |
| `frame` | Sampled `fen`, `sideToMove`, `bucket`, `psqt`, `positional`, `eval`, `l1TopK`, White/Black perspective metadata, and `buffers`. |
| `compare` | `active`; when active: `name`, `eval`, `psqt`, `positional`, `bucket`. |
| `record` | `recording`, `path`, `frames`. |
| `datagen`, `datagenDefaults` | Run counters/settings described below. |

Perspective metadata includes `kingSquare`, `kingBucket`, `mirrored` and
`featureCount`. A `frame` can show a sampled PV leaf while `game` shows the
root board. Read `frame.sideToMove` and `frame.fen` when converting its score.
Search metrics belong to completed search iterations; they are not all-node
traces. JSON numbers representing uint64 counters can exceed JavaScript's exact
integer range; clients requiring exact huge counters need an appropriate policy.

## Controls

Requests are JSON objects. Errors use human-readable messages rather than
versioned error codes. Some missing/wrong-typed arguments select defaults, so
do not treat a 200 reply as proof that arbitrary input was interpreted as intended.

| `cmd` | Fields / behavior |
|---|---|
| `pause` | Boolean `value`; missing/non-boolean defaults true. |
| `step`, `newgame` | Advance a paused session once, or request game reset. |
| `delay` | Integer `value`, nonnegative ms. |
| `nodes` | Integer `value`, nonnegative budget; 0 removes the node cap. |
| `depth` | Integer `value`, clamped 0..`maxDepth`; 0 removes depth cap. |
| `threads` | Integer `value`, clamped 1..hardware threads. |
| `variety` | Integer `value`, nonnegative near-best opening range in cp. |
| `mode` | String `value`: `selfplay`, `analysis`, `human`, `datagen`. |
| `position` | String `fen`, optional string `moves` array; engine validates. |
| `move` | String `value`, legal UCI move for the session. |
| `enginecolor` | Integer `value`, 0 White / 1 Black. |
| `randomopening` | Boolean `value`; wrong type defaults false. |
| `comparenet` | File path in string `value`; empty clears comparison. |
| `record` | File path in `value`; empty stops summary recording. |
| `datagen` | `action` and run fields below. |

Example, against an already-running native viewer:

```bash
curl -sS http://127.0.0.1:7777/api/health
curl -sS -X POST http://127.0.0.1:7777/api/control \
  -H 'Content-Type: application/json' -d '{"cmd":"nodes","value":1000}'
```

Do not remove both depth/node limits accidentally. Controls are asynchronous
session requests; an accepted command is not an acknowledgement that its next
search/position has already been published. Pause can retain a stale displayed
snapshot until another publication; see [limitations](../limitations.md#visualizer-state-publication).

### Datagen controls

`action: "probe"` with `out` returns `ok`, `resumable`, `positions`, `games`
and optional saved `config`. `action: "stop"` stops generation. Other action
strings currently enter the start path; clients should send exactly `start`.

Start accepts `out`, `targetPositions`, `targetGames`, `nodes`, `depth`,
`skipPlies`, `maxPlies`, `openingPlies`, `balance`, `varietyCp`, `varietyPlies`,
`shardPositions`, `lam`, `seed`, `emit` (`raw` or `blend`) and Boolean `resume`.
Defaults are sent in `datagenDefaults`. Resume restores saved row-shaping
settings; requested run targets can extend the old run. Most other controls
are rejected while generation is active; pause and datagen actions remain allowed.

`datagen` state reports `running`, `out`, `positions`, `games`, `target`,
`targetGames`, White `wins/draws/losses`, `positionsPerSec`, `etaMinutes`,
`shard`, and `shardPath`. Read [generation](../datagen.md) for the checkpoint
and integrity limitations; a reported counter is not a verified dataset hash.

## Summary recording and transport boundaries

Recordings are newline-delimited JSON summaries containing sequence/mode, game
index/ply, depth/seldepth, nodes/NPS, search score/PV, neural eval/PSQT/positional/
bucket when active, comparison score/name when active, and candidate move/score
pairs. They do not contain the full binary activation arrays or a video.
The native recorder opens with truncation; choose a new filename to preserve
an old recording. The existing CLI help's append wording is inaccurate.

Filesystem paths resolve with the native process's permissions. WASM has its
own virtual filesystem and cannot be assumed to write arbitrary host paths.
HTTP binds loopback without authentication. This interface is not a public
remote-control service or an authenticated game-server API.
