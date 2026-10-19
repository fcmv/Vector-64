# Deploy the browser engine

The browser build packages the engine, existing NNUE weights and Vector Scope
as static files. It is separate from publishing this documentation site and
from running the native loopback HTTP viewer.

## Build and keep the output together

Use Node 24 for UI changes, and activate an installed Emscripten SDK before
building. Record its exact version with the experiment/deployment. CI currently
uses `latest`; no pinned SDK/browser compatibility matrix is established here.

```bash
source /path/to/emsdk/emsdk_env.sh
emcc --version
bash tools/build_wasm.sh
python -m http.server -d ui/dist-wasm 8080
```

Open `http://localhost:8080`. For a custom output directory, pass it as the
script's argument. Deploy the complete directory, including `index.html`,
`stk-engine.js`, `stk-engine.wasm`, `stk-vector-64.nnue`,
`coi-serviceworker.js` and any worker/runtime companions emitted by the SDK.
Copying only the HTML does not deploy an engine. UI edits require the committed
bundle to be rebuilt using the documented Node toolchain.

## Hosting requirements

Serve over HTTPS, or localhost for development. The current WASM build uses
pthreads and SharedArrayBuffer. It requires cross-origin isolation; suitable
servers can send these response headers:

```text
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

Keep required resources same-origin or supply their appropriate cross-origin
resource permissions. The bundled service worker can provide isolation on
suitable static hosts, but its installation/control may require reloading the
page. Do not bypass browser security errors. In DevTools check
`self.crossOriginIsolated` and `typeof SharedArrayBuffer` after reload.

The service worker needs a valid scope and secure context. If publishing in a
project subdirectory, preserve the generated relative URL layout and test that
scope there. Serve JavaScript and WASM with suitable MIME types. A host returning
the HTML fallback for a missing `.wasm` or weight file can produce a confusing
startup/decode failure even when the request status is 200.

## Transport selection and cache updates

The UI first probes same-origin `/api/health`. A responding native backend uses
the HTTP adapter; otherwise it initializes WASM. The Vite development server
proxies `/api` to native port 7777. A static deployment does not discover an
arbitrary engine running on another localhost port.

Weights are fetched and stored in Cache Storage. Use a versioned deployment
directory/URL for a new model/runtime combination. Reusing a filename can retain
an old cached model; clear the relevant site's cache/service worker during
debugging and verify the loaded model identity. Never cache a partial upload as
an accepted release. Publish the complete file set together and verify a fresh
browser profile as well as a returning cached client.

## Acceptance checks

Record OS/browser versions, SDK, source/UI/network hashes and deployment URL.
Verify first-load initialization, isolation/reload recovery, a completed search,
changing neural frames, cache reuse/update and visible errors for missing runtime
or model files. Compare decoded integer frames with an identified native fixture
before claiming runtime parity. A screenshot of a loaded page alone does not
establish all these properties.

Current CI checks that generated deployable files exist and that the model copy
has the right size. It does not execute a full browser/parity test. The build
has no single-thread fallback when isolation is unavailable. WASM file controls
operate within the runtime's virtual filesystem; native filesystem persistence
must not be assumed. See [troubleshooting](troubleshooting.md#browser-engine-cannot-start).
