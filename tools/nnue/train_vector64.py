#!/usr/bin/env python3
"""Train STK-HalfKA checkpoints using the shared pipeline."""
from cli import training_main

if __name__ == "__main__":
    raise SystemExit(training_main(stage="train"))
