import { decodeState } from "./decode";
import type { EngineSource } from "./source";
import { decodeDatagenProbe } from "./source";
import type { ControlCommand, EngineState } from "./types";

/* Use the native C++ encoder in WASM so both transports share the wire contract. */

interface StkModule {
  ccall: (
    name: string,
    ret: string | null,
    argTypes: string[],
    args: unknown[],
  ) => never | number | string;
  HEAPU8: Uint8Array;
  _malloc(n: number): number;
  _free(p: number): void;
  _stk_viz_seq(): number;
  _stk_viz_encode_state(): number;
  _stk_viz_state_ptr(): number;
}

export interface WasmBootOptions {
  moduleUrl: string;
  netUrl: string;
  nodes?: number;
  threads?: number;
  hashMb?: number;
  delayMs?: number;
  onProgress?: (phase: string, loaded: number, total: number) => void;
}

const NET_CACHE = "stk-vector-64-net-v1";

/* Cache the 46 MB net across visits. */
async function loadNet(
  url: string,
  onProgress?: WasmBootOptions["onProgress"],
): Promise<Uint8Array> {
  const cache = "caches" in self ? await caches.open(NET_CACHE) : null;
  const hit = cache ? await cache.match(url) : null;
  const res = hit ?? (await fetch(url));
  if (!res.ok) throw new Error(`net fetch failed: HTTP ${res.status}`);
  if (!hit && cache) await cache.put(url, res.clone());

  const total = Number(res.headers.get("Content-Length") ?? 0);
  if (!res.body || !onProgress) return new Uint8Array(await res.arrayBuffer());

  const reader = res.body.getReader();
  const chunks: Uint8Array[] = [];
  let got = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    got += value.length;
    onProgress("net", got, total);
  }
  const out = new Uint8Array(got);
  let off = 0;
  for (const c of chunks) {
    out.set(c, off);
    off += c.length;
  }
  return out;
}

export class WasmEngineSource implements EngineSource {
  readonly label = "wasm (in-browser)";
  private mod: StkModule | null = null;
  private stopped = false;

  async boot(opts: WasmBootOptions): Promise<void> {
    opts.onProgress?.("engine", 0, 1);
    const factory = (await import(/* @vite-ignore */ opts.moduleUrl)).default;
    const mod: StkModule = await factory();
    this.mod = mod;
    opts.onProgress?.("engine", 1, 1);

    const net = await loadNet(opts.netUrl, opts.onProgress);

    mod.ccall(
      "stk_viz_init",
      null,
      ["number", "number", "number", "number", "number"],
      [
        opts.nodes ?? 20000,
        opts.threads ?? 1,
        opts.hashMb ?? 32,
        opts.delayMs ?? 300,
        0,
      ],
    );

    const ptr = mod._malloc(net.length);
    mod.HEAPU8.set(net, ptr);
    const ok = mod.ccall(
      "stk_viz_load_net",
      "number",
      ["number", "number"],
      [ptr, net.length],
    );
    mod._free(ptr);
    if (!ok) throw new Error("the engine rejected the net file");

    mod.ccall("stk_viz_start", null, [], []);
  }

  subscribe(onState: (s: EngineState) => void): () => void {
    this.stopped = false;
    let last = -1;
    const tick = () => {
      if (this.stopped || !this.mod) return;
      const seq = this.mod._stk_viz_seq();
      if (seq !== last) {
        last = seq;
        const len = this.mod._stk_viz_encode_state();
        if (len > 0) {
          const ptr = this.mod._stk_viz_state_ptr();
          // Copy out: the engine reuses this buffer on the next encode.
          const bytes = this.mod.HEAPU8.slice(ptr, ptr + len);
          onState(decodeState(bytes.buffer));
        }
      }
      // Poll at frame rate; the engine runs on its own pthread, so this only
      // costs a sequence read when nothing has changed.
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    return () => {
      this.stopped = true;
    };
  }

  async send(cmd: ControlCommand): Promise<boolean> {
    if (!this.mod) return false;
    const okPtr = this.mod._malloc(4);
    this.mod.ccall(
      "stk_viz_control",
      "string",
      ["string", "number"],
      [JSON.stringify(cmd), okPtr],
    );
    const ok = new Int32Array(this.mod.HEAPU8.buffer, okPtr, 1)[0] === 1;
    this.mod._free(okPtr);
    return ok;
  }

  async netInfo(): Promise<unknown> {
    if (!this.mod) return { loaded: false };
    const json = this.mod.ccall("stk_viz_net_info", "string", [], []) as string;
    return JSON.parse(json);
  }

  async probeDatagen(out: string) {
    if (!this.mod) throw new Error("Browser engine is not ready");
    const mod = this.mod;
    const okPtr = mod._malloc(4);
    try {
      const json = mod.ccall("stk_viz_control", "string", ["string", "number"],
        [JSON.stringify({ cmd: "datagen", action: "probe", out }), okPtr]) as string;
      const response = JSON.parse(json);
      if (new Int32Array(mod.HEAPU8.buffer, okPtr, 1)[0] !== 1)
        throw new Error(response.error || "Recovery lookup failed");
      return decodeDatagenProbe(response);
    } finally {
      mod._free(okPtr);
    }
  }
}
