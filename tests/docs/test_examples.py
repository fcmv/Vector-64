from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
from examples.uci_client import UciClient
from tools.nnue.halfka_features import BLACK, WHITE, features_for, parse_fen_pieces

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def binary(variable: str) -> Path:
    configured = os.environ.get(variable)
    if not configured:
        pytest.skip(f"set {variable} to test the executable documentation")
    assert configured is not None
    result = Path(configured).resolve()
    assert result.is_file(), f"{variable} does not exist: {result}"
    return result


def validator(commands: str) -> list[dict]:
    result = subprocess.run(
        [str(binary("VALIDATOR_BIN"))], input=commands + "\nquit\n",
        text=True, capture_output=True, timeout=20, check=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]


def test_example_client_completes_a_real_search():
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples/uci_client.py"), "--engine", str(binary("ENGINE_BIN")),
         "--depth", "3"], text=True, capture_output=True, timeout=40, check=True,
    )
    assert re.search(r"^bestmove [a-h][1-8][a-h][1-8][qrbn]?(?: ponder .*)?$", result.stdout, re.M)


def test_uci_option_table_covers_the_advertised_options():
    document = (ROOT / "docs/uci.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"^\| `([^`]+)` \| (?:spin|string|check|combo) \|", document, re.M))
    for variable in ("ENGINE_BIN", "VALIDATOR_BIN"):
        with UciClient(binary(variable)) as client:
            client.send("uci")
            lines = client.until("uciok")
        advertised = {line.split("option name ", 1)[1].split(" type ", 1)[0]
                      for line in lines if line.startswith("option name ")}
        if variable == "VALIDATOR_BIN":
            assert advertised == documented
        else:
            assert advertised == documented - {"UCI_Variant", "DrawRules", "SearchJson"}


def test_documented_inline_apply_reply_and_nonmutation():
    replies = validator("getfen\napply e2e4 startpos\ngetfen")
    before, moved, after = replies
    assert before == after
    assert moved == {
        "ok": True, "legal": True,
        "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        "sideToMove": "b", "inCheck": False, "terminal": "none", "capturedDropType": None,
    }


def test_documented_error_shapes_and_inline_history():
    malformed, illegal, state, children = validator(
        "apply z9z9 startpos\napply e2e5 startpos\nstatus startpos moves e2e4 e7e5\nchildren startpos"
    )
    assert malformed["ok"] is False and malformed["error"] == "malformed_request"
    assert illegal["ok"] is False and illegal["error"] == "illegal_move"
    assert state["ok"] and state["sideToMove"] == "w" and state["terminal"] == "none"
    assert children["count"] == len(children["children"]) == 20
    assert all(set(child) == {"move", "fen", "sideToMove", "inCheck", "terminal"}
               for child in children["children"])


def test_documented_crazyhouse_capture_reply():
    replies = validator(
        "setoption name UCI_Variant value crazyhouse\n"
        "position startpos moves e2e4 d7d5 e4d5\napply d8d5"
    )
    assert replies[0]["fen"] == "rnb1kbnr/ppp1pppp/8/3q4/8/8/PPPP1PPP/RNBQKBNR[Pp] w KQkq - 0 3"
    assert replies[0]["capturedDropType"] == "p"


def test_worked_halfka_feature_indices_and_example_data():
    pieces, _ = parse_fen_pieces(START)
    white = features_for(pieces, WHITE)
    black = features_for(pieces, BLACK)
    assert len(white) == len(black) == 31
    assert 2120 in white
    assert 2811 in white
    rows = (ROOT / "examples/training_positions.txt").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 8
    for row in rows:
        fen, cp = row.split("|")
        parse_fen_pieces(fen)
        assert -6000 <= float(cp) <= 6000


def test_model_card_identifies_the_actual_shipped_bytes():
    net = ROOT / "nets/stk-vector-64.nnue"
    card = (ROOT / "nets/model-card.md").read_text(encoding="utf-8")
    data = net.read_bytes()
    assert data[:9] == b"STKHALFKA"
    assert struct.unpack("<4I", data[9:25]) == (1, 22528, 1024, 8)
    assert len(data) == 46_997_305
    assert hashlib.sha256(data).hexdigest() in card


def test_perft_divide_documented_total():
    result = subprocess.run(
        [str(binary("ENGINE_BIN")), "--perft-divide", START, "3"],
        text=True, capture_output=True, timeout=20, check=True,
    )
    assert "Total: 8902" in result.stdout
