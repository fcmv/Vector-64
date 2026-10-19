#!/usr/bin/env python3
"""STK-HalfKA training entry point; shares make_net's model and stages."""
from __future__ import annotations

from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parent / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.train_nnue", "ARGV0": __file__}, run_name="__main__")

from .nnue.cli import training_main

if __name__ == "__main__":
    raise SystemExit(training_main())
