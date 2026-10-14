"""Legacy 81920-feature HalfKP contract used by tools/train_nnue.py.

The active C++ engine uses 22528-feature STK-HalfKA (src/nnue/halfka.h).
These tests cover the older Python pipeline, with an optional trainer cross-check.
"""
from __future__ import annotations

import importlib.util
import itertools
import pathlib
import sys

WHITE, BLACK = 0, 1
PIECE_BUCKETS = 10
SQUARES = 64
TOTAL_FEATURES = 81920

def feature_index(king_sq: int, bucket: int, piece_sq: int, perspective: int) -> int:
    """Legacy HalfKP index shared with tools/train_nnue.py."""
    side = 1 if perspective == BLACK else 0
    return (((king_sq * PIECE_BUCKETS + bucket) * SQUARES + piece_sq) * 2) + side

def test_known_values() -> None:
    assert feature_index(0, 0, 0, WHITE) == 0
    assert feature_index(0, 0, 0, BLACK) == 1
    assert feature_index(63, 9, 63, BLACK) == TOTAL_FEATURES - 1

def test_perspective_is_the_low_bit() -> None:
    for k, b, s in [(0, 0, 0), (12, 3, 40), (63, 9, 63)]:
        assert feature_index(k, b, s, WHITE) + 1 == feature_index(k, b, s, BLACK)

def test_all_indices_unique_and_in_range() -> None:
    seen = bytearray(TOTAL_FEATURES)
    count = 0
    for k in range(SQUARES):
        for b in range(PIECE_BUCKETS):
            for s in range(SQUARES):
                for p in (WHITE, BLACK):
                    idx = feature_index(k, b, s, p)
                    assert 0 <= idx < TOTAL_FEATURES
                    assert seen[idx] == 0, "feature index collision"
                    seen[idx] = 1
                    count += 1
    assert count == TOTAL_FEATURES
    assert all(seen)

def test_matches_trainer_when_torch_available() -> None:
    if importlib.util.find_spec("torch") is None:
        import pytest

        pytest.skip("torch not installed; contract verified against reference only")

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from tools.train_nnue import halfkp_feature_index

    for k, b, s, p in itertools.product((0, 7, 63), (0, 4, 9), (0, 33, 63), (WHITE, BLACK)):
        assert halfkp_feature_index(k, b, s, p) == feature_index(k, b, s, p)
