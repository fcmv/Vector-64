#!/usr/bin/env python3
"""Compatibility command for the current STK-HalfKA shard builder."""

from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.nnue.build_halfkp_npz", "ARGV0": __file__}, run_name="__main__")
from .build_stk_data import main

if __name__ == "__main__":
    raise SystemExit(main())
