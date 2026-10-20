import { afterEach, describe, expect, it, vi } from "vitest";
import { HttpEngineSource } from "./httpSource";
import { WasmEngineSource } from "./wasmSource";

afterEach(() => vi.unstubAllGlobals());

describe("datagen recovery transports", () => {
  const probe = { resumable: true, positions: 42, games: 3 };

  it("uses the configured native base and returns the recovery payload", async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => probe });
    vi.stubGlobal("fetch", fetch);
    expect(await new HttpEngineSource("http://engine.test").probeDatagen("dataset")).toEqual(probe);
    expect(fetch).toHaveBeenCalledWith("http://engine.test/api/control", expect.objectContaining({
      body: JSON.stringify({ cmd: "datagen", action: "probe", out: "dataset" }),
    }));
  });

  it.each([false, true])("rejects failed or malformed native probes (HTTP success: %s)", async (ok) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok, status: 400, json: async () => ({}) }));
    await expect(new HttpEngineSource("http://engine.test").probeDatagen("dataset")).rejects.toThrow();
  });

  it.each([true, false])("uses the WASM control reply without HTTP (accepted: %s)", async (accepted) => {
    const heap = new Uint8Array(64);
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const mod = {
      HEAPU8: heap,
      _malloc: vi.fn().mockReturnValue(8),
      _free: vi.fn(),
      ccall: vi.fn((_name: string, _ret: string, _types: string[], args: unknown[]) => {
        new Int32Array(heap.buffer, args[1] as number, 1)[0] = accepted ? 1 : 0;
        return JSON.stringify(accepted ? probe : { error: "unreadable dataset" });
      }),
    };
    const source = new WasmEngineSource();
    Object.assign(source, { mod });
    if (accepted) expect(await source.probeDatagen("browser-data")).toEqual(probe);
    else await expect(source.probeDatagen("browser-data")).rejects.toThrow("unreadable dataset");
    expect(mod._free).toHaveBeenCalledWith(8);
    expect(fetch).not.toHaveBeenCalled();
    expect(mod.ccall).toHaveBeenCalledWith("stk_viz_control", "string", ["string", "number"],
      [JSON.stringify({ cmd: "datagen", action: "probe", out: "browser-data" }), 8]);
  });
});
