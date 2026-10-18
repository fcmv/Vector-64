#!/usr/bin/env python3
"""Validate both supported STK-HalfKA binary network widths."""
from __future__ import annotations

import argparse
from pathlib import Path

from contracts import check_net


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--allow-trailing", action="store_true")
    args = parser.parse_args(argv)
    try:
        info = check_net(args.path, args.allow_trailing)
    except (ValueError, OSError) as error:
        print(f"[FAIL] {error}")
        return 1
    print(f"[PASS] STK-HalfKA {info['hidden']}: {info['size']} bytes, {len(info['sections'])} sections")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
