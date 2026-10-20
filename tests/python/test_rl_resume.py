from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.nnue import rl_loop as rl


def prepared(tmp_path):
    sources = []
    for gen in range(2):
        path = tmp_path / f"data{gen}.txt"
        path.write_text("".join(f"gen{gen}-row{row}\n" for row in range(80)))
        sources.append(path)
    work = tmp_path / "generation"
    work.mkdir()
    return work, sources


def test_generation_resume_preserves_input_and_rejects_changes(tmp_path):
    work, sources = prepared(tmp_path)
    output = rl.generation_input(work, sources, None, 0, 30, 777, 1)
    original = output.read_bytes()
    stamp = output.stat().st_mtime_ns
    assert rl.generation_input(work, sources, None, 0, 30, 777, 1).read_bytes() == original
    assert output.stat().st_mtime_ns == stamp
    with pytest.raises(ValueError, match="configuration"):
        rl.generation_input(work, sources, None, 0, 31, 777, 1)
    output.write_bytes(original + b"tampered\n")
    with pytest.raises(ValueError, match="input changed"):
        rl.generation_input(work, sources, None, 0, 30, 777, 1)


def test_interrupted_input_publication_reconstructs_identical_sampling(tmp_path, monkeypatch):
    work, sources = prepared(tmp_path)
    replace = rl.os.replace

    def interrupt(source, target):
        if Path(target).name == "train_input.txt":
            raise RuntimeError("interrupted before input publication")
        replace(source, target)

    monkeypatch.setattr(rl.os, "replace", interrupt)
    with pytest.raises(RuntimeError, match="interrupted"):
        rl.generation_input(work, sources, None, 0, 30, 777, 1)
    pending = (work / "train_input.txt.tmp").read_bytes()
    assert json.loads((work / "train_input.json").read_text())["sha256"]
    monkeypatch.setattr(rl.os, "replace", replace)
    assert rl.generation_input(work, sources, None, 0, 30, 777, 1).read_bytes() == pending
    other = tmp_path / "uninterrupted"
    other.mkdir()
    assert rl.generation_input(other, sources, None, 0, 30, 777, 1).read_bytes() == pending


def test_source_drift_and_legacy_inputs_are_preserved(tmp_path):
    work, sources = prepared(tmp_path)
    output = rl.generation_input(work, sources, None, 0, 30, 777, 1)
    original = output.read_bytes()
    sources[0].write_text("changed\n")
    with pytest.raises(ValueError, match="source data"):
        rl.generation_input(work, sources, None, 0, 30, 777, 1)
    assert output.read_bytes() == original
    (work / "train_input.json").unlink()
    with pytest.raises(ValueError, match="no sampling manifest"):
        rl.generation_input(work, sources, None, 0, 30, 777, 1)
    assert output.read_bytes() == original
