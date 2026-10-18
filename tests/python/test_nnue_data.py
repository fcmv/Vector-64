from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "nnue"))
import build_stk_data as prep
import contracts as contract

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BLACK = START.replace(" w ", " b ")


def options(source: pathlib.Path, **changes):
    parser = argparse.ArgumentParser()
    prep.add_arguments(parser)
    args = parser.parse_args([])
    args.input = str(source)
    args.shard_size = 1
    for key, value in changes.items():
        setattr(args, key, value)
    return args


def shard(path: pathlib.Path, **changes):
    w, b, stm = prep.encode(START)
    arrays = {"white_indices": w[None, :], "black_indices": b[None, :],
              "stm": np.array([stm]), "eval_cp": np.array([42.0])}
    arrays.update(changes)
    np.savez(path, **arrays)


def test_preparation_preserves_black_target_perspective_and_deduplicates(tmp_path):
    source = tmp_path / "labels.txt"
    source.write_text(f"{START} | 40\n{BLACK} | -70\n{START} | 40\n{{broken\n{BLACK} | nan\n")
    out = prep.prepare(options(source, cp_source="stm"), tmp_path / "data")
    manifest = contract.validate_dataset(out / "manifest.json")
    assert manifest["total_samples"] == 2
    assert manifest["stats"]["duplicate"] == 1
    assert manifest["stats"]["non_finite"] == 1
    assert manifest["stats"]["invalid"] == 1
    assert contract.load_shard(out / manifest["shards"][1]["file"])["eval_cp"].tolist() == [70]
    assert prep.prepare(options(source, cp_source="stm"), out) == out


def test_changed_preparation_inputs_are_rejected(tmp_path):
    source = tmp_path / "labels.txt"
    source.write_text(f"{START} | 40\n")
    out = prep.prepare(options(source), tmp_path / "data")
    with pytest.raises(ValueError, match="settings changed"):
        prep.prepare(options(source, min_depth=2), out)


def test_resume_after_dedup_commit_before_progress_loses_no_rows(tmp_path, monkeypatch):
    source = tmp_path / "labels.txt"
    source.write_text(f"{START} | 40\n{BLACK} | -70\n{START} | 40\n")
    out = tmp_path / "data"
    write = prep.write_json

    def interrupt(path, value):
        if path.name == "progress.json" and len(value["shards"]) == 1:
            raise RuntimeError("simulated power loss")
        write(path, value)

    monkeypatch.setattr(prep, "write_json", interrupt)
    with pytest.raises(RuntimeError, match="power loss"):
        prep.prepare(options(source), out)
    monkeypatch.setattr(prep, "write_json", write)
    prep.prepare(options(source), out)
    assert contract.validate_dataset(out / "manifest.json")["total_samples"] == 2


def test_dedup_keeps_castling_rights_and_ep_state(tmp_path):
    source = tmp_path / "labels.txt"
    source.write_text(f"{START} | 40\n{START.replace('KQkq', '-')} | 70\n")
    out = prep.prepare(options(source), tmp_path / "data")
    assert contract.validate_dataset(out / "manifest.json")["total_samples"] == 2


@pytest.mark.parametrize("changes", [
    {"white_indices": np.zeros((1, 32), dtype=np.float32)},
    {"white_indices": np.full((1, 32), 81919)},
    {"white_indices": np.full((1, 32), -2)},
    {"white_indices": np.full((1, 32), -1)},
    {"white_indices": np.zeros((1, 32), dtype=np.int32)},
    {"black_indices": np.zeros((2, 32), dtype=np.int32)},
    {"eval_cp": np.array([np.nan])}, {"eval_cp": np.array([np.inf])},
    {"eval_cp": np.array([1, 2])}, {"stm": np.array([2])}, {"stm": np.array([0.5])},
])
def test_corrupt_shards_fail_preflight(tmp_path, changes):
    path = tmp_path / "shard.npz"
    shard(path, **changes)
    with pytest.raises(ValueError):
        contract.load_shard(path)


def test_hash_mismatch_is_detected(tmp_path):
    source = tmp_path / "labels.txt"
    source.write_text(f"{START} | 40\n")
    out = prep.prepare(options(source), tmp_path / "data")
    shard(out / "stk_shard_00000.npz", eval_cp=np.array([90.0]))
    with pytest.raises(ValueError, match="SHA256"):
        contract.validate_dataset(out / "manifest.json")


def test_untagged_data_requires_explicit_opt_in(tmp_path):
    path = tmp_path / "manifest.json"
    shard(tmp_path / "shard.npz")
    path.write_text(json.dumps({"total_samples": 1, "shards": [{"file": "shard.npz", "samples": 1}]}))
    with pytest.raises(ValueError, match="untagged"):
        contract.validate_dataset(path)
    assert contract.validate_dataset(path, allow_untagged=True)["total_samples"] == 1


@pytest.mark.parametrize("values", [
    {"total_samples": 7}, {"format": "HalfKP"}, {"target_perspective": "stm"},
    {"shards": [{"file": "../secret.npz", "samples": 1}]},
    {"shards": [{"file": "shard.npz", "samples": 0}]},
    {"shards": [{"file": "shard.npz", "samples": 1}] * 2, "total_samples": 2},
])
def test_bad_manifests_are_rejected(tmp_path, values):
    path = tmp_path / "manifest.json"
    manifest = {"format": contract.DATA_FORMAT, "version": 1, "features": 22528,
                "target_perspective": "white", "total_samples": 1,
                "shards": [{"file": "shard.npz", "samples": 1}]}
    manifest.update(values)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        contract.load_manifest(path)


@pytest.mark.parametrize("hidden,size", [(1024, 46997305), (128, 6510649)])
def test_network_layout_matches_engine_sizes(hidden, size):
    _, actual = contract.net_layout(hidden)
    assert actual == size


@pytest.mark.parametrize("mutation", ["magic", "version", "features", "width", "buckets", "truncate", "trailing"])
def test_invalid_network_files_are_rejected(tmp_path, mutation):
    path = tmp_path / "net.nnue"
    fields = [contract.MAGIC, 1, 22528, 128, 8]
    _, size = contract.net_layout(128)
    index = {"magic": 0, "version": 1, "features": 2, "width": 3, "buckets": 4}.get(mutation)
    if index is not None:
        fields[index] = b"VECTOR64" if index == 0 else 99
    with path.open("wb") as stream:
        stream.write(contract.HEADER.pack(*fields))
        stream.truncate(size + (1 if mutation == "trailing" else -1 if mutation == "truncate" else 0))
    with pytest.raises(ValueError):
        contract.check_net(path)
