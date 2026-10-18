#!/usr/bin/env python3
"""STK-HalfKA training entry point; shares make_net's model and stages."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "nnue"))
from cli import training_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(training_main())
