#!/usr/bin/env python3
"""Run the shared STK-HalfKA preparation, training, export and parity stages."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "nnue"))
from cli import training_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(training_main(workdir="runs/pipeline"))
