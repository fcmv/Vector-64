import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { connect, crossOriginIsolated } from "./connect";
import { HttpEngineSource } from "./httpSource";

const wasm = vi.hoisted(() => ({ boot: vi.fn(), create: vi.fn() }));
vi.mock("./wasmSource", () => ({
  WasmEngineSource: class {
    constructor() { wasm.create(); }
    boot = wasm.boot;
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("location", { href: "https://example.test/index.html" });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));
  vi.stubGlobal("self", { crossOriginIsolated: true });
});
afterEach(() => vi.unstubAllGlobals());

describe("engine transport startup", () => {
  it("uses the native server without requiring browser isolation", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    vi.stubGlobal("self", { crossOriginIsolated: false });
    vi.stubGlobal("SharedArrayBuffer", undefined);
    expect(await connect(vi.fn())).toBeInstanceOf(HttpEngineSource);
    expect(wasm.create).not.toHaveBeenCalled();
  });

  it.each([false, undefined])("rejects missing isolation (%s) before starting WASM", async (isolated) => {
    vi.stubGlobal("self", { crossOriginIsolated: isolated });
    const progress = vi.fn();
    await expect(connect(progress)).rejects.toThrow("Enable cross-origin isolation");
    expect(wasm.create).not.toHaveBeenCalled();
    expect(progress).not.toHaveBeenCalled();
  });

  it("rejects browsers without shared memory", async () => {
    vi.stubGlobal("SharedArrayBuffer", undefined);
    await expect(connect(vi.fn())).rejects.toThrow("cannot start the browser engine");
    expect(wasm.boot).not.toHaveBeenCalled();
  });

  it("boots WASM when isolation and shared memory are available", async () => {
    const progress = vi.fn();
    await connect(progress);
    expect(wasm.boot).toHaveBeenCalledOnce();
    expect(wasm.boot).toHaveBeenCalledWith(expect.objectContaining({
      moduleUrl: "https://example.test/stk-engine.js",
      netUrl: "https://example.test/stk-vector-64.nnue",
    }));
    expect(progress).toHaveBeenCalledWith({ phase: "engine", loaded: 0, total: 1 });
  });

  it("falls back to WASM after a failed native health request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network unavailable")));
    await connect(vi.fn());
    expect(wasm.boot).toHaveBeenCalledOnce();
  });

  it("returns false when no browser global exists", () => {
    vi.stubGlobal("self", undefined);
    expect(crossOriginIsolated()).toBe(false);
  });
});
