# Troubleshooting

## Engine exits or reports an illegal instruction

Check the release CPU profile. The Windows build requires AVX2; Linux v3 needs
the full x86-64-v3 baseline. A binary built with `-march=native` may not run on
another machine. Use the appropriate release or a new portable build tree.
A matching ISA does not alone guarantee a Linux runtime/library baseline.

## I see text instead of a board

The normal executable is a UCI worker. Use a UCI chess GUI, or run
`ChessEngine-viz` for the local browser interface. If you piped `quit` immediately
after `go`, the asynchronous search may have been interrupted. Use the example
client or wait interactively for `bestmove`.

## CMake fetch fails or a target is missing

Default configuration fetches visualization headers. Use `ENGINE_VIZ=OFF` for
an offline engine tree, or provide an accessible dependency source. Check that
`EMBED_NNUE` exists: missing weights can omit embedded-net targets. Variant
binaries require `ENGINE_VARIANTS=ON`. Use separate trees for MSVC and MinGW.

On MSVC, executable paths include `bin/Release/`, and CTest needs `-C Release`.
On Windows, select Git Bash explicitly if CTest invokes the WSL `bash.exe`
launcher. [Building](building.md) gives the full commands.

## A network fails to load or gives unexpected scores

Run the network checker. Supported files have `STKHALFKA` magic and width 1024
for `EvalFile`, 128 for `EvalFileSmall`; a `.nnue` suffix does not establish
compatibility. Older HalfKP or other engines' nets cannot be reinterpreted.

Discard a process after a failed replacement, because rollback is currently
unsafe. In drop variants, NNUE is intentionally suppressed. In isolated small-net
parity, use the classical executable so an embedded big net does not override
`eval`. Network output is mover-relative, not always White-relative.

## Validator replies refer to the wrong position

An invalid two-line setup retains the old resident position. Read the text
setup diagnostic or use `status fen ...` / `apply ... fen ...` inline requests.
An inline request never changes resident state. Set variant/draw policy explicitly
when reusing a worker. A final FEN does not include repetition history.

Do not treat `canmate` or material-draw status as complete adjudication; read
[the counterexample](limitations.md#material-adjudication).

## Tablebase search ignores a root restriction or behaves oddly in a variant

Clear `SyzygyPath` before using a required `go searchmoves` restriction or
searching a drop variant. Current root ranking can replace the filtered move
list, and the probing path has no explicit runtime-variant guard. Switching
`UCI_Variant` does not unload tables. See [tablebase limitations](limitations.md#tablebase-search).

For standard positions, confirm table coverage and the engine's load diagnostic.
An interior WDL call requires a zero halfmove counter and no castling rights;
missing data falls back to normal search. `readyok` is not proof that a
particular endgame is covered.

## Browser engine cannot start

Determine the transport first. The UI probes same-origin `/api/health`; it does
not discover arbitrary local ports. The Vite development server proxies `/api`
to the native server at port 7777. A static WASM deployment needs its engine
module, wasm, weights, isolation shim, and generated page together.

Use localhost or HTTPS, permit the service worker, and verify
`self.crossOriginIsolated` plus `SharedArrayBuffer` in the browser console.
The current pthread build has no single-thread fallback. If an old net remains
in browser cache after replacing files at the same URL, clear the site's Cache
Storage or use a versioned deployment path. Native visualization does not need
cross-origin isolation. [Vector Scope](visualizer.md) covers setup.

## Training resume is refused or results look too good

Use a new workdir when changing dataset identity, width or saved settings.
`--init` is a fresh warm start; resume restores compatible training state.
Do not override tagged dataset checks to load old HalfKP arrays. Check label
perspective and leakage between training/validation positions. A successful
layout/parity check is not held-out quality or match strength.

For a report, include the minimal commands and environment described in
[support](support.md), plus the first actual error rather than only the last
wrapper failure.
