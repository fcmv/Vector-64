#!/usr/bin/env bash
# Emscripten pthreads require SharedArrayBuffer and COOP/COEP. The service
# worker shim supplies isolation on static hosts; the UI reports unsupported hosts.
#
# Usage: source /path/to/emsdk/emsdk_env.sh
#        bash tools/build_wasm.sh [output-dir]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/ui/dist-wasm}"
BUILD="$ROOT/build-wasm"
NET="$ROOT/nets/stk-vector-64.nnue"

command -v emcmake >/dev/null 2>&1 || {
  echo "emcmake not found -- source emsdk_env.sh first" >&2
  exit 2
}
[ -f "$NET" ] || {
  echo "missing net: $NET" >&2
  exit 2
}

# -msimd128 lets the compiler vectorise the portable scalar NNUE kernels. We do
# NOT hand-write wasm_simd128 kernels: the project's rule is that any SIMD path
# must be proven bit-exact against the scalar reference by test_zobrist, and
# that gate has to run under node before such a path can be trusted.
FLAGS=(
  -O3
  -msimd128
  -pthread
  -sPTHREAD_POOL_SIZE=4
  -sALLOW_MEMORY_GROWTH=1
  -sINITIAL_MEMORY=268435456
  -sMAXIMUM_MEMORY=2147483648
  -sMODULARIZE=1
  -sEXPORT_ES6=1
  -sEXPORT_NAME=createStkEngine
  -sENVIRONMENT=web,worker
  -sEXPORTED_RUNTIME_METHODS=ccall,cwrap,HEAPU8
  -sEXPORTED_FUNCTIONS=_malloc,_free,_stk_viz_init,_stk_viz_load_net,_stk_viz_start,_stk_viz_stop,_stk_viz_seq,_stk_viz_encode_state,_stk_viz_state_ptr,_stk_viz_control,_stk_viz_net_info
)

echo "[wasm] configuring"
emcmake cmake -S "$ROOT" -B "$BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DENGINE_NATIVE=OFF \
  -DENGINE_LTO=OFF \
  -DENGINE_VIZ=OFF >/dev/null

# The viz sources need nlohmann/json. The native configure already fetches it;
# reuse that copy when present, otherwise pull the same pinned header.
JSON_DIR="$(dirname "$(find "$ROOT" -name json.hpp -path '*_deps*' 2>/dev/null | head -1)")"
if [ ! -f "$JSON_DIR/json.hpp" ]; then
  JSON_DIR="$BUILD/third_party"
  mkdir -p "$JSON_DIR"
  curl -fsSL -o "$JSON_DIR/json.hpp"     https://raw.githubusercontent.com/nlohmann/json/v3.11.3/single_include/nlohmann/json.hpp
fi

echo "[wasm] building chess_core + viz telemetry"
cmake --build "$BUILD" --target chess_core -j

mkdir -p "$OUT"
echo "[wasm] linking stk-engine.js"
em++ "${FLAGS[@]}" \
  -I "$ROOT/src" \
  "$ROOT/src/viz/probe.cpp" \
  "$ROOT/src/viz/session.cpp" \
  "$ROOT/src/viz/wire.cpp" \
  "$ROOT/src/viz/wasm_bindings.cpp" \
  "$BUILD/libchess_core.a" \
  -I "$JSON_DIR" \
  -o "$OUT/stk-engine.js"

cp "$NET" "$OUT/stk-vector-64.nnue"
cp "$ROOT/ui/public/coi-serviceworker.js" "$OUT/"

# Ship the UI beside the engine, with the COOP/COEP shim injected as the first
# script so SharedArrayBuffer (and therefore pthreads) is available before the
# engine module loads. Injected here rather than in ui/index.html so the native
# build, which needs none of this, stays untouched.
if [ -f "$ROOT/ui/dist/index.html" ]; then
  sed 's|<head>|<head><script src="coi-serviceworker.js"></script>|'     "$ROOT/ui/dist/index.html" > "$OUT/index.html"
  echo "[wasm] UI copied with the cross-origin-isolation shim"
else
  echo "[wasm] WARNING ui/dist/index.html missing -- run 'npm run build' in ui/"
fi

echo "[wasm] done -> $OUT"
ls -la "$OUT"
echo
echo "Serve $OUT over HTTP (the service worker needs a real origin):"
echo "  python -m http.server -d $OUT 8080"
