from __future__ import annotations

import argparse
import os
import pathlib
import sys

import numpy as np
import pytest

torch = pytest.importorskip("torch")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "nnue"))
import build_stk_data as prep
import export_vector64 as exporter
import make_net as mk
import rl_train_vector64 as rl
from contracts import check_net, sha256

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@pytest.fixture(autouse=True)
def cpu_threads():
    previous = torch.get_num_threads()
    torch.set_num_threads(2)
    yield
    torch.set_num_threads(previous)


def test_replay_encoder_matches_training_and_counts_enemy_king():
    for fen in (START, START.replace(" w ", " b ")):
        w, b, stm = rl.encode_halfka(fen, 32)
        ew, eb, es = prep.encode(fen)
        np.testing.assert_array_equal(w, ew)
        np.testing.assert_array_equal(b, eb)
        assert stm == es
        assert (w >= 0).sum() == 31


def test_replay_training_updates_exportable_stknet(tmp_path):
    torch.manual_seed(1)
    model = mk.STKNet(hidden=128)
    replay = rl.ReplayBuffer(8, 32)
    w, b, stm = prep.encode(START)
    replay.add_batch(w[None], b[None], np.array([stm]), np.array([500.0], dtype=np.float32))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    previous = model.outb.detach().clone()
    loss, mae = rl.train_step(model, optimizer, None, replay, batch_size=1,
                              device=torch.device("cpu"), amp_enabled=False, scaler=None)
    assert np.isfinite(loss) and np.isfinite(mae)
    assert not torch.equal(previous, model.outb)
    path = tmp_path / "float.pt"
    torch.save({"state_dict": model.state_dict()}, path)
    assert check_net(mk.stage_export(tmp_path, path))["hidden"] == 128


def test_legacy_checkpoint_is_rejected_with_retraining_message(tmp_path):
    path = tmp_path / "legacy.pt"
    torch.save({"state_dict": {"feature_transform.weight": torch.zeros(1)}}, path)
    with pytest.raises(ValueError, match="retrain"):
        mk.load_float_model(path)


def test_non_finite_weights_cannot_be_exported(tmp_path):
    model = mk.STKNet(hidden=128)
    with torch.no_grad():
        model.outb[0] = float("nan")
    path = tmp_path / "float.pt"
    torch.save({"state_dict": model.state_dict()}, path)
    with pytest.raises(ValueError, match="non-finite"):
        mk.stage_export(tmp_path, path)
    assert not (tmp_path / "stk_halfka_128.nnue").exists()


def test_complete_pipeline_resume_and_export_parity(tmp_path):
    engine = os.environ.get("ENGINE_BIN")
    if not engine:
        pytest.skip("set ENGINE_BIN for pipeline engine parity")
    source = tmp_path / "data.txt"
    source.write_text(f"{START} | 40\n{START.replace(' w ', ' b ')} | -70\n")
    work = tmp_path / "run"
    output = tmp_path / "candidate.nnue"
    command = ["--input", str(source), "--workdir", str(work), "--hidden", "128",
               "--epochs", "1", "--batch-size", "2", "--device", "cpu", "--engine", engine,
               "--shard-size", "1", "--output", str(output), "--tolerance-cp", "0"]
    assert mk.main(command) == 0
    original = sha256(output)
    assert mk.main(command) == 0
    assert sha256(output) == original
    with pytest.raises(ValueError, match="settings changed"):
        mk.main(command + ["--lr", "0.002"])
    assert exporter.main(["--checkpoint", str(work / "model_float.pt"), "--output", str(output),
                          "--engine", engine]) == 0
    assert sha256(output) == original


def test_parity_requires_an_engine(tmp_path, monkeypatch):
    monkeypatch.setattr(mk, "find_engine", lambda _: None)
    with pytest.raises(ValueError, match="engine binary required"):
        mk.stage_verify(argparse.Namespace(engine=None), tmp_path / "float.pt", tmp_path / "net.nnue")


def test_interrupted_training_resumes_to_identical_weights(tmp_path, monkeypatch):
    source = tmp_path / "data.txt"
    source.write_text(f"{START} | 40\n{START.replace(' w ', ' b ')} | -70\n")
    parser = argparse.ArgumentParser()
    prep.add_arguments(parser)
    args = parser.parse_args(["--shard-size", "1"])
    args.input = str(source)
    data = prep.prepare(args, tmp_path / "data")
    common = ["--data-dir", str(data), "--hidden", "128", "--stage", "train", "--epochs", "1",
              "--batch-size", "1", "--device", "cpu"]
    baseline, resumed = tmp_path / "baseline", tmp_path / "resumed"
    mk.main(common + ["--workdir", str(baseline)])
    load = mk.load_shard
    calls = 0

    def interrupt(path):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("interrupted training")
        return load(path)

    monkeypatch.setattr(mk, "load_shard", interrupt)
    with pytest.raises(RuntimeError, match="interrupted training"):
        mk.main(common + ["--workdir", str(resumed)])
    monkeypatch.setattr(mk, "load_shard", load)
    mk.main(common + ["--workdir", str(resumed)])
    expected = mk.load_float_model(baseline / "model_float.pt").state_dict()
    actual = mk.load_float_model(resumed / "model_float.pt").state_dict()
    assert all(torch.equal(expected[key], actual[key]) for key in expected)
