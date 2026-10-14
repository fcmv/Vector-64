import { useEffect, useRef, useState } from "react";
import type { EngineState } from "./types";

export interface PlyRecord {
  ply: number;
  /** Evaluation in centipawns, always from White's point of view. */
  evalWhite: number;
  move: string;
  fen: string;
  depth: number;
  seldepth: number;
  nodes: number;
  nps: number;
}

export interface IterRecord {
  depth: number;
  seldepth: number;
  nodes: number;
  ply: number;
}

/* The engine streams snapshots without history. Keep a bounded record here
   and reset it when the game or position changes. */
export function useGameHistory(state: EngineState | null) {
  const [plies, setPlies] = useState<PlyRecord[]>([]);
  const [iters, setIters] = useState<IterRecord[]>([]);
  const lastPly = useRef(-1);
  const lastGame = useRef(-1);
  const lastIter = useRef("");

  useEffect(() => {
    if (!state) return;
    const g = state.game;

    if (g.gameIndex !== lastGame.current || g.ply < lastPly.current) {
      lastGame.current = g.gameIndex;
      lastPly.current = g.ply;
      setPlies([]);
      setIters([]);
      return;
    }

    if (g.ply !== lastPly.current) {
      lastPly.current = g.ply;
      // The frame is captured at the PV leaf, so convert with ITS side to move.
      const evalWhite = state.frame
        ? state.frame.eval * (state.frame.sideToMove === 0 ? 1 : -1)
        : state.search.scoreCp * (g.fen.split(" ")[1] === "b" ? -1 : 1);
      setPlies((p) =>
        [
          ...p,
          {
            ply: g.ply,
            evalWhite,
            move: g.lastMove,
            fen: g.fen,
            depth: state.search.depth,
            seldepth: state.search.seldepth,
            nodes: state.search.nodes,
            nps: state.search.nps,
          },
        ].slice(-400),
      );
    }

    const key = `${g.ply}:${state.search.depth}:${state.search.nodes}`;
    if (state.search.depth > 0 && key !== lastIter.current) {
      lastIter.current = key;
      setIters((it) =>
        [
          ...it,
          {
            depth: state.search.depth,
            seldepth: state.search.seldepth,
            nodes: state.search.nodes,
            ply: g.ply,
          },
        ].slice(-160),
      );
    }
  }, [state]);

  return { plies, iters };
}
