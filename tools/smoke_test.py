#!/usr/bin/env python3
"""Preflight STK-HalfKA data, optimization, export and engine parity."""
from __future__ import annotations

import argparse
import math
import tempfile
from pathlib import Path

import numpy as np
import torch

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parent / "_entrypoint.py"),
                   init_globals={"MODULE": "tools.smoke_test", "ARGV0": __file__}, run_name="__main__")

from .nnue import build_stk_data as prep
from .nnue import make_net as mk
from .nnue.contracts import check_net, validate_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=None, help="raw labels or prepared manifest.json")
    parser.add_argument("--engine", default=None)
    parser.add_argument("--hidden", type=int, choices=(128, 1024), default=128)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--allow-untagged-shards", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)
    engine = mk.find_engine(args.engine)
    if engine is None or not engine.is_file():
        parser.error("build an engine and pass --engine for parity")
    if args.data:
        source = Path(args.data)
        manifest = source / "manifest.json" if source.is_dir() else source
        if manifest.name == "manifest.json":
            info = validate_dataset(manifest, args.allow_untagged_shards)
            print(f"[PASS] dataset: {info['total_samples']} checked rows")
        else:
            valid = 0
            for index, line in enumerate(prep.input_lines(args.data)):
                if index >= 1000:
                    break
                try:
                    parsed = prep.parse_line(line, 0)
                    if parsed is not None and math.isfinite(parsed[1]):
                        prep.encode(parsed[0])
                        valid += 1
                except (ValueError, TypeError, KeyError, IndexError):
                    continue
            if not valid:
                raise ValueError("no usable labelled FENs in first 1000 lines")
            print(f"[PASS] raw data sample: {valid} usable rows")
    torch.manual_seed(42)
    device = torch.device(args.device)
    model = mk.STKNet(hidden=args.hidden).to(device)
    encoded = [prep.encode(fen) for fen in mk.BENCH_FENS]
    white = torch.from_numpy(np.stack([row[0] for row in encoded])).long().to(device)
    black = torch.from_numpy(np.stack([row[1] for row in encoded])).long().to(device)
    stm = torch.tensor([row[2] for row in encoded], device=device)
    bucket = torch.clamp((white >= 0).sum(dim=1) // 4, 0, mk.BUCKETS - 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss = (torch.sigmoid(model(white, black, stm, bucket) / mk.CP_SCALE) - 0.5).square().mean()
    loss.backward()
    if not torch.isfinite(loss) or any(p.grad is not None and not torch.isfinite(p.grad).all()
                                      for p in model.parameters()):
        raise ValueError("non-finite forward or gradients")
    optimizer.step()
    model.clip_weights()
    print(f"[PASS] {args.device}: forward, backward, optimizer")
    with tempfile.TemporaryDirectory(prefix="stk-preflight-") as directory:
        work = Path(directory)
        checkpoint = work / "model_float.pt"
        torch.save({"state_dict": model.state_dict()}, checkpoint)
        net = mk.stage_export(work, checkpoint)
        check_net(net)
        mk.stage_verify(argparse.Namespace(engine=str(engine), tolerance_cp=0), checkpoint, net)
    print("[PASS] STK-HalfKA preflight complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
