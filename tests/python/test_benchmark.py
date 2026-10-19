from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.bench import benchmark as bench


def sample(nps=1000):
    return {"nodes": 1000, "elapsed_ms": 1000000 // nps, "nps": nps}


@pytest.fixture
def collector(tmp_path, monkeypatch):
    monkeypatch.setattr(bench.time, "sleep", lambda _: None)
    args = argparse.Namespace(output=tmp_path, retries=1, drift_percent=5.0, cooldown=0.0,
                              retry_delay=0.0, canary_samples=3, warmups=0, repeats=2, timeout=2.0)
    binary = tmp_path / "engine"
    binary.write_bytes(b"fixture")
    identity = {"source_commit": "fixture", "depth": 13, "threads": 1, "hash_mb": 8,
                "bench_source_sha256": "fixture", "drift_percent": 5.0, "repeats": 2,
                "canary": {"executable": str(binary), "sha256": bench.sha256(binary), "expected_nodes": 1000},
                "machine": {"fixture": True},
                "workloads": [{"label": "classical", "kind": "search", "executable": str(binary),
                               "sha256": bench.sha256(binary), "expected_nodes": 1000}]}
    state = {"identity": identity, "status": "new", "events": [], "accepted": {}, "baseline": {"nps": 1000}}
    return bench.Collector(args, identity, state)


@pytest.mark.parametrize("rate,expected", [(900, -10), (1100, 10), (1000, 0)])
def test_canary_detects_speedups_and_slowdowns(rate, expected):
    assert bench.drift_percent(rate, 1000) == pytest.approx(expected)


def test_search_rejects_wrong_fingerprint_and_inconsistent_timing():
    assert bench.parse_search("bench depth 13 nodes 1000 time 500ms nps 2000", 13, 1000)["nps"] == 2000
    for output in ("bench depth 13 nodes 1001 time 500ms nps 2002",
                   "bench depth 13 nodes 1000 time 0ms nps 0",
                   "bench depth 13 nodes 1000 time 500ms nps 1999", "no reply"):
        with pytest.raises(bench.InvalidResult):
            bench.parse_search(output, 13, 1000)


def test_perft_checks_actual_counts_even_when_footer_claims_success():
    rows = [f"{mode} : {index} nodes | 0.100s | 0 MNPS"
            for index in range(1, 7) for mode in ("Single", "Multi")]
    output = "RESULTS: 6 Passed, 0 Failed\n" + "\n".join(rows)
    assert len(bench.parse_perft(output, list(range(1, 7)))) == 12
    with pytest.raises(bench.InvalidResult):
        bench.parse_perft(output.replace("Single : 1 nodes", "Single : 2 nodes"), list(range(1, 7)))


def test_pre_drift_skips_payload_and_retains_failed_attempt(collector, monkeypatch):
    canaries = iter([sample(800), sample(), sample()])
    monkeypatch.setattr(collector, "canary", lambda _: next(canaries))
    payload_calls = []
    monkeypatch.setattr(collector, "payload", lambda *_: payload_calls.append(1) or sample())
    collector.measure(collector.identity["workloads"][0], "run1-classical")
    attempts = [event for event in collector.state["events"] if event["kind"] == "sample_attempt"]
    assert [event["accepted"] for event in attempts] == [False, True]
    assert attempts[0]["reason"] == "pre_canary_drift"
    assert payload_calls == [1]


def test_post_drift_discards_payload_instead_of_correcting_it(collector, monkeypatch):
    canaries = iter([sample(), sample(800), sample(), sample()])
    payloads = iter([sample(500), sample(1000)])
    monkeypatch.setattr(collector, "canary", lambda _: next(canaries))
    monkeypatch.setattr(collector, "payload", lambda *_: next(payloads))
    collector.measure(collector.identity["workloads"][0], "run1-classical")
    assert collector.state["accepted"]["run1-classical"]["payload"]["nps"] == 1000
    assert collector.state["events"][0]["reason"] == "post_canary_drift"
    assert collector.state["events"][0]["payload"]["nps"] == 500


def test_timeout_exhausts_bounded_retries_and_preserves_checkpoint(collector, monkeypatch):
    def timeout(_):
        raise subprocess.TimeoutExpired("fixture", 0.1)
    monkeypatch.setattr(collector, "canary", timeout)
    with pytest.raises(bench.UnstableMachine):
        collector.measure(collector.identity["workloads"][0], "run1-classical")
    assert len(collector.state["events"]) == 2
    checkpoint = json.loads((collector.output / "partial.json").read_text())
    assert checkpoint["accepted"] == {}
    assert all(event["reason"] == "process_failure" for event in checkpoint["events"])


def test_correctness_failure_is_not_retried(collector, monkeypatch):
    monkeypatch.setattr(collector, "canary", lambda _: sample())
    def wrong(*_):
        raise bench.InvalidResult("wrong nodes")
    monkeypatch.setattr(collector, "payload", wrong)
    with pytest.raises(bench.InvalidResult, match="wrong nodes"):
        collector.measure(collector.identity["workloads"][0], "run1-classical")
    assert not collector.state["accepted"]
    assert not collector.state["events"]


def test_calibration_never_rebases_after_machine_slowdown(collector, monkeypatch):
    monkeypatch.setattr(collector, "canary", lambda _: sample(800))
    with pytest.raises(bench.UnstableMachine):
        collector.calibrate()
    assert collector.state["baseline"]["nps"] == 1000
    assert all(not event["accepted"] for event in collector.state["events"])


def test_unstable_initial_calibration_creates_no_baseline(collector, monkeypatch):
    collector.state["baseline"] = None
    rates = iter([1000, 1000, 800, 1100] * 2)
    monkeypatch.setattr(collector, "canary", lambda _: sample(next(rates)))
    with pytest.raises(bench.UnstableMachine):
        collector.calibrate()
    assert collector.state["baseline"] is None


def test_resume_skips_accepted_work_and_writes_complete_summary(collector, monkeypatch):
    collector.state["accepted"]["run1-classical"] = {
        "kind": "search", "label": "classical", "payload": sample(), "event_id": 0}
    monkeypatch.setattr(collector, "calibrate", lambda: None)
    monkeypatch.setattr(collector, "canary", lambda _: sample())
    calls = []
    monkeypatch.setattr(collector, "payload", lambda _, name: calls.append(name) or sample())
    collector.collect()
    assert calls == ["run2-classical"]
    assert json.loads((collector.output / "results.json").read_text())["status"] == "complete"
    assert "Rejected attempts retained: 0" in (collector.output / "summary.md").read_text()


def test_resume_refuses_changed_identity(collector):
    collector.save()
    collector.args.resume = True
    collector.args.canary_reference = None
    identity = copy.deepcopy(collector.identity)
    identity["canary"]["sha256"] = "different"
    with pytest.raises(bench.InvalidResult, match="identity/settings changed"):
        bench.load_state(collector.args, identity, {})


def test_reference_baseline_requires_same_machine_and_canary(collector):
    reference = collector.output / "reference.json"
    identity = copy.deepcopy(collector.identity)
    identity["machine"] = {"different": True}
    bench.atomic_json(reference, {"identity": identity, "baseline": {"nps": 1000}})
    directory = collector.output / "new"
    directory.mkdir()
    collector.args.output = directory
    collector.args.resume = False
    collector.args.canary_reference = reference
    with pytest.raises(bench.InvalidResult, match="reference machine/binary/workload differs"):
        bench.load_state(collector.args, collector.identity, {})


def test_atomic_checkpoint_failure_preserves_previous_json(tmp_path, monkeypatch):
    path = tmp_path / "partial.json"
    bench.atomic_json(path, {"version": 1})
    def blocked(*_):
        raise PermissionError("replace blocked")
    monkeypatch.setattr(bench.os, "replace", blocked)
    with pytest.raises(PermissionError):
        bench.atomic_json(path, {"version": 2})
    assert json.loads(path.read_text()) == {"version": 1}


def test_output_directory_lock_refuses_second_writer(tmp_path):
    with bench.run_lock(tmp_path), pytest.raises(bench.InvalidResult, match="another collector"):
        with bench.run_lock(tmp_path):
            pytest.fail("second writer entered")


def test_binary_replacement_during_run_stops_before_launch(collector):
    binary = Path(collector.identity["canary"]["executable"])
    binary.write_bytes(b"changed")
    with pytest.raises(bench.InvalidResult, match="executable changed"):
        collector.execute(binary, [], "fixture")


def test_interrupted_run_stays_resumable_and_never_emits_results(collector, monkeypatch):
    def interrupted():
        raise KeyboardInterrupt
    monkeypatch.setattr(collector, "calibrate", interrupted)
    with pytest.raises(KeyboardInterrupt):
        collector.collect()
    state = json.loads((collector.output / "partial.json").read_text())
    assert state["status"] == "interrupted"
    assert not (collector.output / "results.json").exists()


def test_failed_process_preserves_output(collector):
    with pytest.raises(subprocess.CalledProcessError):
        collector.execute(Path(sys.executable), ["-c", "print('fixture'); raise SystemExit(3)"], "fake")
    assert "fixture" in next(collector.output.glob("*-fake.txt")).read_text()
    assert collector.state["events"][0]["status"] == "failed"


def test_timeout_kills_fake_child_and_saves_log(collector):
    collector.args.timeout = 0.1
    with pytest.raises(subprocess.TimeoutExpired):
        collector.execute(Path(sys.executable),
                          ["-c", "import time; print('started', flush=True); time.sleep(30)"], "timeout")
    assert collector.state["events"][0]["error_type"] == "TimeoutExpired"


def test_resume_keeps_accepted_bracket_and_rejects_tampered_payload(collector, monkeypatch):
    monkeypatch.setattr(collector, "canary", lambda _: sample())
    monkeypatch.setattr(collector, "payload", lambda *_: sample())
    collector.measure(collector.identity["workloads"][0], "run1-classical")
    collector.args.resume = True
    collector.args.canary_reference = None
    loaded = bench.load_state(collector.args, collector.identity, {})
    assert loaded["accepted"]["run1-classical"]["payload"] == sample()
    loaded["accepted"]["run1-classical"]["payload"]["nps"] = 2000
    bench.atomic_json(collector.output / "partial.json", loaded)
    with pytest.raises(bench.InvalidResult, match="does not match its acceptance event"):
        bench.load_state(collector.args, collector.identity, {})


def test_complete_checkpoint_cannot_omit_samples(collector):
    collector.state["status"] = "complete"
    with pytest.raises(bench.InvalidResult, match="missing samples"):
        bench.validate_state(collector.state, collector.identity)


def test_initial_stable_calibration_creates_persistent_median(collector, monkeypatch):
    collector.state["baseline"] = None
    values = iter([sample(), sample(990), sample(1000), sample(1010)])
    monkeypatch.setattr(collector, "canary", lambda _: next(values))
    collector.calibrate()
    saved = json.loads((collector.output / "partial.json").read_text())
    assert saved["baseline"]["nps"] == 1000
    assert saved["events"][0]["accepted"]


def test_bracket_guard_rejects_swing_even_with_both_endpoints_near_baseline(collector, monkeypatch):
    canaries = iter([sample(960), sample(1040), sample(), sample()])
    monkeypatch.setattr(collector, "canary", lambda _: next(canaries))
    monkeypatch.setattr(collector, "payload", lambda *_: sample())
    collector.measure(collector.identity["workloads"][0], "run1-classical")
    assert collector.state["events"][0]["reason"] == "bracket_drift"
    assert collector.state["events"][0]["bracket_drift_percent"] > 5
    assert len(collector.state["accepted"]) == 1
