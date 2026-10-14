// Mirrors the wire format produced by src/viz/wire.cpp. Keep the two in step:
// the C++ side is the source of truth for field names and buffer order.

export interface Arch {
  hidden: number;
  pair: number;
  l1: number;
  l2: number;
  psqtBuckets: number;
  kingBuckets: number;
  pieceKinds: number;
  features: number;
  actMax: number;
}

export interface GameState {
  fen: string;
  startFen: string;
  moves: string[];
  lastMove: string;
  ply: number;
  over: boolean;
  result: string;
  reason: string;
  gameIndex: number;
  wins: number;
  draws: number;
  losses: number;
  /** Human-mode clocks, milliseconds remaining. */
  whiteMs: number;
  blackMs: number;
  clockRunning: boolean;
}

export interface Candidate {
  move: string;
  scoreCp: number;
  pv: string[];
}

export interface SearchInfo {
  depth: number;
  seldepth: number;
  scoreCp: number;
  nodes: number;
  tbHits: number;
  elapsedMs: number;
  nps: number;
  pv: string[];
  qsearchTtHitRate: number;
  negamaxTtHitRate: number;
  /** Ranked best first. Empty when the engine is running single-PV. */
  candidates: Candidate[];
}

export interface PerspectiveInfo {
  kingSquare: number;
  kingBucket: number;
  mirrored: boolean;
  featureCount: number;
}

/** One active input feature, decoded from the flat i32 stream (6 per feature). */
export interface ActiveFeature {
  square: number;
  orientedSquare: number;
  pieceColor: number;
  pieceType: number;
  pieceKind: number;
  featureIndex: number;
}

export interface Frame {
  fen: string;
  sideToMove: number;
  bucket: number;
  psqt: number;
  positional: number;
  eval: number;
  l1TopK: number;
  white: PerspectiveInfo;
  black: PerspectiveInfo;

  accUs: Int16Array;
  accThem: Int16Array;
  l1in: Uint8Array;
  l1out: Uint8Array;
  l2out: Uint8Array;

  /** Attribution: weight * activation, exact integers. */
  outContrib: Int32Array;
  l2Contrib: Int32Array;
  /** [neuron][k] pairs of (sourceIndex, contribution), neuron-major. */
  l1Top: Int32Array;

  whiteFeatures: ActiveFeature[];
  blackFeatures: ActiveFeature[];
}

export type Mode = "selfplay" | "analysis" | "human" | "datagen";

export interface DatagenState {
  running: boolean;
  out: string;
  positions: number;
  games: number;
  target: number;
  /** Game cap, or 0 when only the position target applies. */
  targetGames: number;
  wins: number;
  draws: number;
  losses: number;
  positionsPerSec: number;
  etaMinutes: number;
  /* shard is the current index; shardPath names its file in the dataset directory. */
  shard: number;
  shardPath: string;
}

export interface DatagenOptions {
  out: string;
  targetPositions: number;
  /** Stop after this many games too; 0 = only the position target decides. */
  targetGames: number;
  nodes: number;
  depth: number;
  emit: "raw" | "blend";
  lam: number;
  skipPlies: number;
  maxPlies: number;
  openingPlies: number;
  balance: number;
  seed: number;
  /** Rows per shard file; 0 writes a single file at `out`. */
  shardPositions: number;
  resume?: boolean;
}

/* Engine-reported state includes CLI recordings and failed opens. */
export interface RecordState {
  recording: boolean;
  path: string;
  frames: number;
}

/**
 * What a probe found on disk. `config` is the settings the existing run was
 * built with; a resume reuses them, so the form's own values do not apply.
 * Absent for a dataset written before the settings were recorded.
 */
export interface DatagenProbe {
  resumable: boolean;
  positions: number;
  games: number;
  config?: {
    nodes: number;
    depth: number;
    skipPlies: number;
    maxPlies: number;
    openingPlies: number;
    balance: number;
    varietyCp: number;
    varietyPlies: number;
    shardPositions: number;
    lam: number;
    emit: "raw" | "blend";
    seed: number;
  };
}

export interface DatagenDefaults {
  out: string;
  targetPositions: number;
  targetGames: number;
  nodes: number;
  depth: number;
  emit: "raw" | "blend";
  lam: number;
  skipPlies: number;
  maxPlies: number;
  openingPlies: number;
  balance: number;
  /** Rows per shard file; 0 writes a single file. */
  shardPositions: number;
  seed: number;
}

export interface EngineState {
  seq: number;
  mode: Mode;
  running: boolean;
  paused: boolean;
  thinking: boolean;
  nnueActive: boolean;
  threads: number;
  /* 0 always plays best; nonzero variety chooses near-equal scored moves
     only during the configured opening plies. */
  varietyCp: number;
  hardwareThreads: number;
  maxDepth: number;
  engineColor: number;
  arch: Arch;
  game: GameState;
  search: SearchInfo;
  legalMoves: string[];
  frame: Frame | null;
  datagen: DatagenState;
  datagenDefaults: DatagenDefaults;
  record: RecordState;
}

export type ControlCommand =
  | { cmd: "pause"; value: boolean }
  | { cmd: "step" }
  | { cmd: "newgame" }
  | { cmd: "delay"; value: number }
  | { cmd: "nodes"; value: number }
  | { cmd: "threads"; value: number }
  | { cmd: "variety"; value: number }
  /** A path starts recording; empty stops it. */
  | { cmd: "record"; value: string }
  | { cmd: "randomopening"; value: boolean }
  | { cmd: "depth"; value: number }
  | ({ cmd: "datagen"; action: "start" } & DatagenOptions)
  | { cmd: "datagen"; action: "stop" }
  | { cmd: "enginecolor"; value: number }
  | { cmd: "mode"; value: Mode }
  | { cmd: "position"; fen: string; moves: string[] }
  | { cmd: "move"; value: string };
