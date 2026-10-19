from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import benchmark as bench
import benchmark_matrix as matrix


def workload(**overrides):
    return {"label": "fixture", "kind": "search", "depth": 13, "threads": 1,
            "hash_mb": 8, "multipv": 1, "expected_nodes": 1000, **overrides}


def reply(nodes=1000, depth=13):
    return f"info string bench depth {depth} nodes {nodes} time 100ms nps {nodes * 10}"


def test_focused_plan_varies_one_axis_and_keeps_canonical_anchor():
    rows = matrix.configurations([8, 13, 16], [1, 2, 4], [8, 64], [1, 3], False)
    assert rows[0] == (13, 1, 8, 1)
    assert len(rows) == 7
    assert all(sum(a != b for a, b in zip(row, rows[0], strict=True)) <= 1 for row in rows)
    assert len(rows) == len(set(rows))


def test_full_plan_is_the_requested_cartesian_product():
    rows = matrix.configurations([8, 10], [1, 2], [8, 64], [1, 3], True)
    assert len(rows) == 16
    assert (10, 2, 64, 3) in rows
    assert all(row[0] != 13 for row in rows)


@pytest.mark.parametrize("value", ["0", "1,-1", "1,no", "65", ""])
def test_invalid_matrix_values_are_rejected(value):
    with pytest.raises(bench.InvalidResult):
        matrix.positive_values(value, 64)


def test_canonical_profile_requires_committed_count_but_threaded_counts_can_vary():
    with pytest.raises(bench.InvalidResult, match="fingerprint"):
        matrix.parse_matrix_search(reply(nodes=1001), workload())
    assert matrix.parse_matrix_search(reply(nodes=1001), workload(threads=2))["nodes"] == 1001
    with pytest.raises(bench.InvalidResult):
        matrix.parse_matrix_search(reply(depth=12), workload())
    with pytest.raises(bench.InvalidResult):
        matrix.parse_matrix_search(reply() + reply(), workload())


def test_matrix_payload_sends_actual_options_and_checks_repeat_consistency(tmp_path, monkeypatch):
    args = argparse.Namespace(output=tmp_path)
    state = {"events": [], "accepted": {}}
    collector = matrix.MatrixCollector(args, {}, state)
    calls = []
    outputs = iter([reply(nodes=1001, depth=10), reply(nodes=1002, depth=10)])

    def execute(binary, arguments, name, stdin):
        calls.append(stdin)
        return next(outputs)

    monkeypatch.setattr(collector, "execute", execute)
    spec = workload(depth=10, hash_mb=64, multipv=3, executable="fixture")
    assert collector.payload(spec, "sample")["nodes"] == 1001
    assert "Threads value 1\nsetoption name Hash value 64\nsetoption name MultiPV value 3\nbench 10" in calls[0]
    with pytest.raises(bench.InvalidResult, match="nodes changed"):
        collector.payload(spec, "sample2")


def test_matrix_payload_rejects_option_error(tmp_path, monkeypatch):
    collector = matrix.MatrixCollector(argparse.Namespace(output=tmp_path), {}, {"events": []})
    monkeypatch.setattr(collector, "execute", lambda *_: "info string setoption Threads: invalid value\n" + reply())
    with pytest.raises(bench.InvalidResult, match="rejected a matrix option"):
        collector.payload(workload(executable="fixture"), "sample")


def test_signature_gates_use_canonical_search_before_canary_calibration(tmp_path, monkeypatch):
    collector = matrix.MatrixCollector(argparse.Namespace(output=tmp_path),
                                       {"engine_profiles": [{"executable": "fixture", "expected_nodes": 1000,
                                                             "label": "classical"}]}, {})
    calls = []
    monkeypatch.setattr(collector, "search", lambda *args: calls.append(args))
    monkeypatch.setattr(bench.Collector, "calibrate", lambda _: calls.append("calibration"))
    collector.calibrate()
    assert calls == [(Path("fixture"), 1000, "signature-classical"), "calibration"]


def test_plan_never_launches_a_process_or_creates_output(tmp_path, monkeypatch, capsys):
    args = argparse.Namespace(matrix={"plan": True}, output=tmp_path / "unused", repeats=5,
                              warmups=1, canary_samples=3)
    identity = {"workloads": [workload()]}
    monkeypatch.setattr(matrix, "arguments", lambda _: args)
    monkeypatch.setattr(matrix, "make_identity", lambda _: (identity, {}))
    monkeypatch.setattr(matrix.MatrixCollector, "collect", lambda _: pytest.fail("plan launched collector"))
    assert matrix.main([]) == 0
    assert not args.output.exists()
    assert '"measured_samples": 5' in capsys.readouterr().out


def test_summary_reports_threaded_node_ranges_not_one_fixed_count():
    identity = {"workloads": [workload(threads=2)], "source_commit": "fixture", "drift_percent": 5}
    state = {"identity": identity, "baseline": {"nps": 1000}, "events": [], "accepted": {}}
    for index, nodes in enumerate([1000, 1100]):
        state["accepted"][str(index)] = {"label": "fixture", "payload": {"nodes": nodes, "elapsed_ms": 100,
                                                                        "nps": nodes * 10}}
    assert "1,050 (1,000-1,100)" in matrix.render_summary(copy.deepcopy(state))


def test_matrix_resume_validates_saved_counts_and_timing():
    spec = workload(depth=10)
    identity = {"workloads": [spec], "repeats": 1, "drift_percent": 5}
    payload = {"nodes": 1000, "elapsed_ms": 100, "nps": 10000}
    event = {"kind": "sample_attempt", "sample_id": "run1-fixture", "accepted": True, "warmup": False,
             "payload": payload, "before": {"nps": 1000}, "after": {"nps": 1000}}
    state = {"baseline": {"nps": 1000}, "status": "complete", "events": [event], "matrix_nodes": {"fixture": 1000},
             "accepted": {"run1-fixture": {"label": "fixture", "payload": payload, "event_id": 1}}}
    matrix.validate_matrix_state(state, identity)
    state["matrix_nodes"]["fixture"] = 1001
    with pytest.raises(bench.InvalidResult, match="consistency mismatch"):
        matrix.validate_matrix_state(state, identity)
    state["matrix_nodes"]["fixture"] = 1000
    payload["nps"] = 1
    with pytest.raises(bench.InvalidResult, match="timing"):
        matrix.validate_matrix_state(state, identity)
