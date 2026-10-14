import type { ControlCommand, EngineState } from "./types";

/* Components share this interface across native HTTP and browser WASM transports. */
export interface EngineSource {
  subscribe(onState: (s: EngineState) => void): () => void;
  /** Send a control command. Resolves false if the engine rejected it. */
  send(cmd: ControlCommand): Promise<boolean>;
  netInfo(): Promise<unknown>;
  readonly label: string;
}

export type ConnectionState = "connecting" | "live" | "error";
