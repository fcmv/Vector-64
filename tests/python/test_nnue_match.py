from __future__ import annotations

import builtins
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "nnue"))
import match


def test_worker_failure_is_an_error_not_a_rejected_candidate(tmp_path, monkeypatch, capsys):
    validator = tmp_path / "validator"
    validator.touch()

    class Referee:
        def __init__(self, *args):
            pass

        def quit(self):
            pass

    def broken_engine(*args):
        raise RuntimeError("engine crashed")

    monkeypatch.setattr(match, "Arbiter", Referee)
    monkeypatch.setattr(match, "generate_openings", lambda *args: [""])
    monkeypatch.setattr(match, "Engine", broken_engine)
    assert match.main(["--engine", "broken", "--arbiter", str(validator), "--games", "2",
                       "--concurrency", "1", "--sprt", "0", "5"]) == 3
    assert "engine crashed" in capsys.readouterr().err


@pytest.mark.parametrize("option", ["--games", "--nodes", "--max-plies", "--concurrency"])
def test_zero_match_limits_fail_before_starting_workers(option):
    with pytest.raises(SystemExit) as error:
        match.main(["--engine", "missing", option, "0"])
    assert error.value.code == 2


@pytest.mark.parametrize("score,expected", [(3.0, 0), (-3.0, 1)])
def test_sprt_preserves_bound_decision_after_final_llr_drifts(tmp_path, monkeypatch, score, expected):
    validator = tmp_path / "validator"
    validator.touch()

    class Participant:
        def __init__(self, *args):
            pass

        def quit(self):
            pass

    final_reported = False

    class Tally(match.Tally):
        def llr(self, *args):
            return score if self.n >= 20 and not final_reported else 0.0

        def elo(self):
            return 0.0, 0.0

    def capture_print(*args, **kwargs):
        nonlocal final_reported
        if args and str(args[0]).startswith("final:"):
            final_reported = True
        builtins.print(*args, **kwargs)

    monkeypatch.setattr(match, "Arbiter", Participant)
    monkeypatch.setattr(match, "Engine", Participant)
    monkeypatch.setattr(match, "generate_openings", lambda *args: [""] * 15)
    monkeypatch.setattr(match, "play_game", lambda *args: "1/2-1/2")
    monkeypatch.setattr(match, "Tally", Tally)
    monkeypatch.setattr(match, "print", capture_print, raising=False)
    assert match.main(["--engine", "fake", "--arbiter", str(validator), "--games", "30",
                       "--concurrency", "1", "--sprt", "0", "5"]) == expected
