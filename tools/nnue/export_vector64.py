#!/usr/bin/env python3
"""Export STKNet checkpoints with the engine's fixed quantization contract."""
from __future__ import annotations

from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.nnue.export_vector64", "ARGV0": __file__}, run_name="__main__")

import argparse

from . import make_net as mk
from .contracts import check_net, copy_file, sha256, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--engine", default=None)
    parser.add_argument("--tolerance-cp", type=int, default=0)
    parser.add_argument("--meta", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.tolerance_cp < 0:
        parser.error("tolerance-cp must be nonnegative")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    net = mk.stage_export(args.output.parent, args.checkpoint)
    if args.engine:
        mk.stage_verify(args, args.checkpoint, net)
    if args.output.resolve() != net.resolve():
        copy_file(net, args.output)
    info = check_net(args.output)
    info.update(sha256=sha256(args.output), checkpoint_sha256=sha256(args.checkpoint),
                engine_parity=bool(args.engine))
    write_json(args.meta or args.output.with_suffix(args.output.suffix + ".meta.json"), info)
    print(f"Exported {args.output}; engine parity {'passed' if args.engine else 'not requested'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
