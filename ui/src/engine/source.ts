import type { ControlCommand, DatagenProbe, EngineState } from "./types";

/* Components share this interface across native HTTP and browser WASM transports. */
export interface EngineSource {
  subscribe(onState: (s: EngineState) => void): () => void;
  /** Send a control command. Resolves false if the engine rejected it. */
  send(cmd: ControlCommand): Promise<boolean>;
  probeDatagen(out: string): Promise<DatagenProbe>;
  netInfo(): Promise<unknown>;
  readonly label: string;
}

export type ConnectionState = "connecting" | "live" | "error";

export function decodeDatagenProbe(value: unknown): DatagenProbe {
  const probe = value as Partial<DatagenProbe> | null;
  if (!probe || typeof probe.resumable !== "boolean" ||
      typeof probe.positions !== "number" || !Number.isFinite(probe.positions) || probe.positions < 0 ||
      typeof probe.games !== "number" || !Number.isFinite(probe.games) || probe.games < 0) {
    throw new Error("Invalid datagen recovery response");
  }
  return probe as DatagenProbe;
}
