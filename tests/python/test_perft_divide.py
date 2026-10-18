from __future__ import annotations

import os
import subprocess

import pytest

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def run(*args):
    engine = os.environ.get("ENGINE_BIN")
    if not engine:
        pytest.skip("set ENGINE_BIN to the current build")
    return subprocess.run([engine, "--perft-divide", *args], capture_output=True,
                          input="", text=True, timeout=10, check=False)


def test_perft_divide_prints_each_root_and_total():
    result = run(START, "3")
    assert result.returncode == 0
    rows = dict(line.split(": ") for line in result.stdout.splitlines())
    assert len(rows) == 21
    assert rows.pop("Total") == "8902"
    assert rows["e2e4"] == "600"
    assert sum(map(int, rows.values())) == 8902


@pytest.mark.parametrize("args", [
    (), (START,), (START, "1", "extra"), ("invalid", "1"),
    (START, "-1"), (START, "1junk"), (START, "2147483648"), (START, ""),
])
def test_invalid_perft_divide_arguments_fail(args):
    result = run(*args)
    assert result.returncode == 2
    assert "[ERROR]" in result.stderr
    assert "Total:" not in result.stdout
