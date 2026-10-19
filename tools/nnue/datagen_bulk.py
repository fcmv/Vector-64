#!/usr/bin/env python3
"""Resumable position-capped batches of native STK-HalfKA self-play.

A completed chunk is recorded atomically; interrupted chunks are regenerated.
"""

from __future__ import annotations

from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.nnue.datagen_bulk", "ARGV0": __file__}, run_name="__main__")

import argparse
import json
import subprocess
import sys
import time

from .contracts import check_net, sha256, write_json

HERE = Path(__file__).resolve().parent

def count_lines(path: Path) -> int:
    n = 0
    with path.open("rb") as fh:
        for _ in fh:
            n += 1
    return n

def run_chunk(cmd: list[str], log) -> None:
    log.write("\n$ " + " ".join(cmd) + "\n")
    log.flush()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()  # else Tee-Object block-buffers the pipe (no live output)
        log.write(line)
        log.flush()
    proc.wait()
    if proc.returncode != 0:
        raise SystemExit(f"datagen chunk failed ({proc.returncode})")

def main() -> int:
    p = argparse.ArgumentParser(description="Bulk resumable self-play datagen.")
    p.add_argument("--engine", required=True)
    p.add_argument("--net", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--target-positions", type=int, default=500_000_000)
    p.add_argument("--nodes", type=int, default=5000,
                   help="nodes/move (lower = more throughput; WDL carries the signal)")
    p.add_argument("--lam", type=float, default=0.5,
                   help="WDL blend weight (only used by --emit blend)")
    p.add_argument("--emit", choices=("blend", "raw"), default="raw",
                   help="shard line format: raw = bullet's '<fen> | <eval> | <wdl>' "
                        "(default); blend = '<fen> | <cp>' for the PyTorch trainer")
    p.add_argument("--concurrency", type=int, default=10)
    p.add_argument("--chunk-games", type=int, default=40000,
                   help="games per chunk == crash-recovery granularity")
    p.add_argument("--log-interval", type=float, default=30.0,
                   help="seconds between datagen progress heartbeat lines")
    p.add_argument("--seed-base", type=int, default=100_000)
    args = p.parse_args()

    if min(args.target_positions, args.chunk_games, args.nodes, args.concurrency) <= 0:
        p.error("position, game, node and concurrency limits must be positive")
    if not Path(args.engine).is_file():
        p.error("engine binary not found")
    check_net(Path(args.net))
    config = {"engine": str(Path(args.engine).resolve()), "net_sha256": sha256(Path(args.net)),
              "nodes": args.nodes, "lam": args.lam, "emit": args.emit, "concurrency": args.concurrency,
              "chunk_games": args.chunk_games, "seed_base": args.seed_base}
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    state_path = out / "bulk_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state.get("config") != config:
            raise ValueError("datagen resume settings changed; use a new output directory")
        for chunk in state["chunks"]:
            if sha256(out / chunk["file"]) != chunk["sha256"]:
                raise ValueError("completed datagen chunk changed")
    else:
        state = {"chunks": [], "positions": 0, "config": config}
        if list(out.glob("shard_*.txt")):
            raise ValueError("unregistered datagen chunks; use a new directory")
        write_json(state_path, state)
    log = open(out / "datagen_bulk.log", "a", encoding="utf-8")

    t_start = time.time()
    done0 = state["positions"]
    print(f"[bulk] target {args.target_positions:,} positions @ {args.nodes} nodes; "
          f"have {state['positions']:,} in {len(state['chunks'])} shards", flush=True)

    while state["positions"] < args.target_positions:
        idx = len(state["chunks"])
        shard = out / f"shard_{idx:04d}.txt"
        seed = args.seed_base + idx
        # NNUE, and the chess rules live only in the engine.
        cmd = [str(Path(args.engine).resolve()), "datagen", "--net", args.net,
               "--games", str(args.chunk_games), "--nodes", str(args.nodes),
               "--lam", str(args.lam), "--emit", args.emit,
               "--threads", str(args.concurrency),
               "--log-interval", str(args.log_interval),
               "--seed", str(seed), "--out", str(shard)]
        run_chunk(cmd, log)
        got = count_lines(shard)
        if got == 0:
            raise ValueError("datagen produced no positions; refusing an endless empty-chunk loop")
        state["chunks"].append({"file": shard.name, "seed": seed, "positions": got, "sha256": sha256(shard)})
        state["positions"] += got
        write_json(state_path, state)

        el = time.time() - t_start
        made = state["positions"] - done0
        rate = made / max(el, 1e-9)
        remain = max(0, args.target_positions - state["positions"])
        eta_h = remain / max(rate, 1e-9) / 3600
        print(f"[bulk] chunk {idx}: +{got:,} pos  total {state['positions']:,}/"
              f"{args.target_positions:,}  {rate:.0f} pos/s  eta {eta_h:.1f} h",
              flush=True)

    print(f"[bulk] DONE {state['positions']:,} positions in {len(state['chunks'])} "
          f"shards -> {out}")
    log.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
