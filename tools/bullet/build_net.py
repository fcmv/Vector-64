#!/usr/bin/env python3
"""Build an engine-ready net from self-play shards.

Stages resume from existing outputs. Hold the last shard out for validation;
select a checkpoint by held-out loss, then transfer, export and check engine parity.
A 500M-position run needs roughly 45 GB of text plus 16-48 GB scratch.
Intermediates are removed after train.bin is ready unless --keep-scratch is set.
Use tools/nnue/match.py for the final SPRT.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

def run(cmd: list, cwd: Path | None = None) -> None:
    print(f"\n$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(f"command failed ({r.returncode}): {cmd[0]}")

def exists(p: Path) -> bool:
    return p.exists() and p.stat().st_size > 0

def main() -> int:
    p = argparse.ArgumentParser(description="Build the final .nnue from self-play shards.")
    p.add_argument("--bullet", required=True, help="bullet clone dir (has target/release + examples)")
    p.add_argument("--data-dir", default="runs/bulk/data", help="dir of shard_*.txt")
    p.add_argument("--scratch", default="runs/bulk/bin", help="dir for .bin intermediates")
    p.add_argument("--workdir", default="runs/bulk/train", help="output dir for model_float.pt + .nnue")
    p.add_argument("--engine", default="build-bench/bin/ChessEngine.exe")
    p.add_argument("--epochs", type=int, default=30,
                   help="passes over the dataset. A shard is held out for validation "
                        "loss each superbatch -- watch it: still dropping = train more, "
                        "risen from its min = overfit (transfer an earlier stk-N checkpoint)")
    p.add_argument("--batch", type=int, default=16384)
    p.add_argument("--shuffle-mem-mb", type=int, default=8192)
    p.add_argument("--keep-scratch", action="store_true", help="don't delete .bin intermediates")
    args = p.parse_args()

    bullet = Path(args.bullet).resolve()
    utils = bullet / "target/release/bullet-utils.exe"
    if not utils.exists():
        utils = bullet / "target/release/bullet-utils"
    if not utils.exists():
        raise SystemExit(f"bullet-utils not built at {utils} (cargo build -r --package bullet-utils)")

    data = Path(args.data_dir)
    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)

    # Hold the last shard out for validation; accept plain .txt files from older datasets.
    shards = sorted(data.glob("shard_*.txt")) or sorted(data.glob("*.txt"))
    if len(shards) < 2:
        raise SystemExit(
            f"need >=2 .txt datasets in {data} (the last is held out for "
            f"validation, so one file alone cannot be used); found {len(shards)}"
        )
    val_shard, train_shards = shards[-1], shards[:-1]

    def convert(txt: Path, out: Path) -> None:
        if exists(out):
            print(f"[1/5] {out.name} exists, skip")
        else:
            run([utils, "convert", "--from", "text", "--input", txt.resolve(), "--output", out.resolve()])

    bins = [scratch / (s.stem + ".bin") for s in train_shards]
    for s, b in zip(train_shards, bins, strict=True):
        convert(s, b)

    combined = scratch / "combined.bin"
    if not exists(combined):
        run([utils, "interleave", *[b.resolve() for b in bins], "--output", combined.resolve()])

    trainbin = scratch / "train.bin"
    if not exists(trainbin):
        run([utils, "shuffle", "--input", combined.resolve(),
             "--mem-used-mb", str(args.shuffle_mem_mb), "--output", trainbin.resolve()])

    if not args.keep_scratch:
        for b in bins:
            b.unlink(missing_ok=True)
        combined.unlink(missing_ok=True)

    positions = trainbin.stat().st_size // 32
    bps = max(1, positions // args.batch)
    print(f"\n[4/5] training: {positions:,} positions, {args.epochs} epochs x {bps} batches/superbatch")

    # Skip an existing final checkpoint; otherwise clear stale checkpoints so
    # selection considers only this run.
    final_ckpt = bullet / f"checkpoints/stk-{args.epochs}" / "raw.bin"
    if exists(final_ckpt):
        print(f"[4/5] {final_ckpt.parent.name} exists, skip training")
    else:
        for d in (bullet / "checkpoints").glob("stk-*"):
            shutil.rmtree(d, ignore_errors=True)
        run(["cargo", "run", "-r", "--example", "stk_train", "--features", "cuda", "--",
             str(trainbin.resolve()), str(args.epochs), str(bps)], cwd=bullet)

    print("\n[5/5] selecting best checkpoint by held-out validation loss + export")
    run([sys.executable, str(HERE / "pick_checkpoint.py"), "--bullet", bullet,
         "--val", val_shard.resolve(), "--workdir", args.workdir, "--engine", args.engine])

    net = Path(args.workdir) / "stk_halfka_1024.nnue"
    print("\n==================  DONE  ==================")
    print(f"Final net (best checkpoint by val loss): {net}")
    print("If [val] said the min was the last checkpoint, val loss was still")
    print("dropping -> rerun build_net with a higher --epochs for more.")
    print("Then SPRT vs runs/v2 (the only verdict that counts):")
    print(f"  python tools/nnue/match.py --engine {args.engine} --base-engine {args.engine} \\")
    print(f"      --net {net} --base-net runs/v2/stk_halfka_1024.nnue \\")
    print("      --sprt 0 5 --games 12000 --nodes 10000 --concurrency 10")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
