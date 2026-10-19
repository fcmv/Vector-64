#!/usr/bin/env python3
"""STK-HalfKA feature encoder (reference implementation).

Mirrors src/nnue/halfka.h exactly. Used both as the training-data encoder and
as the parity oracle for the C++ inference path. See the header for the scheme.

Squares: a1=0, file 0=a, rank 0=rank 1 (sq = rank*8 + file), matching Core.
Colours: WHITE=0, BLACK=1. Piece types: PAWN=1..KING=6.
"""

from __future__ import annotations

from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.nnue.halfka_features", "ARGV0": __file__}, run_name="__main__")

import sys

KING_BUCKETS = 32
PIECE_KINDS = 11
SQUARES = 64
FEATURES = KING_BUCKETS * PIECE_KINDS * SQUARES  # 22528

WHITE, BLACK = 0, 1
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6

_PIECE_TYPE = {"p": PAWN, "n": KNIGHT, "b": BISHOP, "r": ROOK, "q": QUEEN, "k": KING}


def flip_rank(sq: int) -> int:
    return sq ^ 56


def flip_file(sq: int) -> int:
    return sq ^ 7


def orient_sq(sq: int, side: int, mirror: bool) -> int:
    s = sq if side == WHITE else flip_rank(sq)
    return flip_file(s) if mirror else s


def make_orient(side: int, king_sq: int) -> tuple[int, bool, int]:
    ok = king_sq if side == WHITE else flip_rank(king_sq)
    mirror = (ok & 7) >= 4
    tk = flip_file(ok) if mirror else ok
    bucket = (tk >> 3) * 4 + (tk & 7)
    return side, mirror, bucket


def piece_kind(side: int, piece_color: int, pt: int) -> int:
    if piece_color == side:
        if pt == KING:
            return -1
        return pt - 1
    return 4 + pt


def feature_index(orient: tuple[int, bool, int], piece_color: int, pt: int, sq: int) -> int:
    side, mirror, bucket = orient
    kind = piece_kind(side, piece_color, pt)
    if kind < 0:
        return -1
    ts = orient_sq(sq, side, mirror)
    return (bucket * PIECE_KINDS + kind) * SQUARES + ts


def parse_fen_pieces(fen: str) -> tuple[list[tuple[int, int, int]], int]:
    """Return ([(sq, color, type)], side_to_move)."""
    parts = fen.strip().split()
    if len(parts) != 6 or parts[1] not in ("w", "b"):
        raise ValueError("expected six FEN fields and w/b side to move")
    board_field, stm_field = parts[0], parts[1]
    ranks = board_field.split("/")
    if len(ranks) != 8:
        raise ValueError("expected eight FEN ranks")
    if parts[2] != "-" and (any(c not in "KQkq" for c in parts[2]) or len(set(parts[2])) != len(parts[2])):
        raise ValueError("invalid castling rights")
    if parts[3] != "-" and (len(parts[3]) != 2 or parts[3][0] not in "abcdefgh" or parts[3][1] not in "36"):
        raise ValueError("invalid en passant square")
    if int(parts[4]) < 0 or int(parts[5]) < 1:
        raise ValueError("invalid FEN clocks")
    for row in ranks:
        width = 0
        for token in row:
            if token in "12345678":
                width += int(token)
            elif token.lower() in _PIECE_TYPE:
                width += 1
            else:
                raise ValueError("unsupported FEN piece")
        if width != 8:
            raise ValueError("FEN rank must contain eight squares")
    pieces: list[tuple[int, int, int]] = []
    rank, file = 7, 0
    for ch in board_field:
        if ch == "/":
            rank -= 1
            file = 0
        elif ch.isdigit():
            file += int(ch)
        else:
            pt = _PIECE_TYPE[ch.lower()]
            color = WHITE if ch.isupper() else BLACK
            pieces.append((rank * 8 + file, color, pt))
            file += 1
    if len(pieces) > 32 or any(sum(c == side and t == KING for _, c, t in pieces) != 1 for side in (WHITE, BLACK)):
        raise ValueError("expected both kings and at most 32 pieces")
    stm = WHITE if stm_field == "w" else BLACK
    return pieces, stm


def features_for(pieces: list[tuple[int, int, int]], perspective: int) -> list[int]:
    king_sq = next(sq for sq, c, t in pieces if t == KING and c == perspective)
    orient = make_orient(perspective, king_sq)
    out = []
    for sq, color, pt in pieces:
        f = feature_index(orient, color, pt, sq)
        if f >= 0:
            out.append(f)
    return sorted(out)


def _main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        pieces, _stm = parse_fen_pieces(line)
        for tag, persp in (("W", WHITE), ("B", BLACK)):
            feats = features_for(pieces, persp)
            assert all(0 <= f < FEATURES for f in feats), "feature out of range"
            print(tag + "".join(f" {f}" for f in feats))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
