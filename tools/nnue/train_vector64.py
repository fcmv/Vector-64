#!/usr/bin/env python3
"""Train STK-HalfKA checkpoints using the shared pipeline."""

from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.nnue.train_vector64", "ARGV0": __file__}, run_name="__main__")
from .cli import training_main

if __name__ == "__main__":
    raise SystemExit(training_main(stage="train"))
