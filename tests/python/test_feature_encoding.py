"""STK-HalfKA feature contract independent of PyTorch."""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "nnue"))
import halfka_features as hk

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@pytest.mark.parametrize("side,king,color,piece,square,expected", [
    (0, 4, 0, 1, 12, 2123), (0, 4, 1, 6, 60, 2811),
    (0, 4, 0, 6, 4, -1), (1, 60, 1, 1, 52, 2123),
    (1, 60, 0, 1, 12, 2483), (1, 60, 1, 6, 60, -1),
    (0, 0, 1, 6, 63, 703), (0, 59, 1, 6, 63, 22527),
])
def test_known_engine_indices(side, king, color, piece, square, expected):
    assert hk.feature_index(hk.make_orient(side, king), color, piece, square) == expected


@pytest.mark.parametrize("side", [hk.WHITE, hk.BLACK])
def test_canonical_buckets_cover_every_feature_once(side):
    indices = []
    for rank in range(8):
        for file in range(4):
            king = rank * 8 + file
            if side == hk.BLACK:
                king ^= 56
            orient = hk.make_orient(side, king)
            for color in (0, 1):
                for piece in range(1, 7):
                    if color == side and piece == hk.KING:
                        continue
                    for square in range(64):
                        indices.append(hk.feature_index(orient, color, piece, square))
    assert sorted(indices) == list(range(22528))


def test_enemy_king_is_included_in_start_position():
    pieces, _ = hk.parse_fen_pieces(START)
    for side in (0, 1):
        features = hk.features_for(pieces, side)
        assert len(features) == 31
        assert len(set(features)) == 31


@pytest.mark.parametrize("fen", [START, "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 b - - 0 1"])
def test_colour_swap_preserves_movers_features(fen):
    pieces, stm = hk.parse_fen_pieces(fen)
    mirrored = [(square ^ 56, color ^ 1, piece) for square, color, piece in pieces]
    assert hk.features_for(pieces, stm) == hk.features_for(mirrored, stm ^ 1)


@pytest.mark.parametrize("fen", [
    "", "8/8/8/8/8/8/8/8 w - - 0 1", "8/8/8/8/8/8/4k3/4K3 x - - 0 1",
    "8/8/8/8/8/8/4k3/4K2 w - - 0 1", "8/8/8/8/8/8/4k3/4K3 w - - 0",
    "8/8/8/8/8/8/4k3/4K3 w X - 0 1", "8/8/8/8/8/8/4k3/4K3 w - a9 0 1",
    "8/8/8/8/8/8/4k3/4K3 w - - -1 1", "8/8/8/8/8/8/4k3/4K3 w - - 0 0",
    "8/8/8/8/8/8/4k3/4KK2 w - - 0 1", "8/8/8/8/8/8/4k3/4X3 w - - 0 1",
])
def test_malformed_fen_is_rejected(fen):
    with pytest.raises(ValueError):
        hk.parse_fen_pieces(fen)
