"""Collect resumable chess benchmarks guarded by a fixed machine-drift canary."""
from __future__ import annotations

from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.bench.benchmark", "ARGV0": __file__}, run_name="__main__")

import argparse
import hashlib
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BENCH = re.compile(r"bench depth (\d+) nodes (\d+) time (\d+)ms nps (\d+)")
PERFT = re.compile(r"(Single|Multi)\s*:\s*(\d+) nodes \| ([\d.]+)s \| (\d+) MNPS")


class InvalidResult(ValueError):
    """A correctness or identity failure that must not be retried."""


class UnstableMachine(RuntimeError):
    """The run cannot continue within the configured drift/retry limits."""


class RunBusy(InvalidResult):
    """Another process owns the output directory."""


def now() -> str:
    return datetime.now().astimezone().isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


@contextmanager
def run_lock(directory: Path):
    with (directory / "run.lock").open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RunBusy("another collector holds this output directory") from error
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == "win32":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def summary(values: list[int] | list[float]) -> dict[str, float]:
    return {"median": statistics.median(values), "min": min(values), "max": max(values)}


def parse_search(stdout: str, depth: int, expected_nodes: int) -> dict[str, int]:
    matches = BENCH.findall(stdout)
    if len(matches) != 1:
        raise InvalidResult("expected exactly one complete search benchmark reply")
    got_depth, nodes, elapsed_ms, nps = map(int, matches[0])
    if got_depth != depth or nodes != expected_nodes:
        raise InvalidResult(f"search fingerprint mismatch: depth={got_depth}, nodes={nodes}; expected {expected_nodes}")
    if elapsed_ms <= 0 or nps != nodes * 1000 // elapsed_ms:
        raise InvalidResult("invalid search timing or NPS")
    return {"nodes": nodes, "elapsed_ms": elapsed_ms, "nps": nps}


def parse_perft(stdout: str, expected: list[int]) -> list[dict[str, Any]]:
    if "RESULTS: 6 Passed, 0 Failed" not in stdout:
        raise InvalidResult("perft suite did not pass all six positions")
    rows = [{"mode": mode, "nodes": int(nodes), "seconds": float(seconds), "reported_mnps": int(mnps)}
            for mode, nodes, seconds, mnps in PERFT.findall(stdout)]
    if len(rows) != 2 * len(expected):
        raise InvalidResult("incomplete perft timing output")
    for index, row in enumerate(rows):
        if row["nodes"] != expected[index // 2] or row["mode"] != ("Single" if index % 2 == 0 else "Multi"):
            raise InvalidResult("perft count/order differs from the committed EPD")
        if row["seconds"] <= 0:
            raise InvalidResult("perft timing rounded to zero; cannot report meaningful throughput")
    return rows


def drift_percent(sample_nps: float, baseline_nps: float) -> float:
    return (sample_nps / baseline_nps - 1.0) * 100.0


def machine_identity(environment: dict[str, Any]) -> dict[str, Any]:
    return {"platform": platform.platform(), "processor": platform.processor(), "logical_processors": os.cpu_count(),
            **{key: environment.get(key) for key in ("cpu", "os")}}


class Collector:
    def __init__(self, args: argparse.Namespace, identity: dict[str, Any], state: dict[str, Any]):
        self.args, self.identity, self.state = args, identity, state
        self.output = args.output

    def save(self) -> None:
        self.state["updated_at"] = now()
        atomic_json(self.output / "partial.json", self.state)

    def event(self, kind: str, **fields: Any) -> dict[str, Any]:
        record = {"id": len(self.state["events"]) + 1, "at": now(), "kind": kind, **fields}
        self.state["events"].append(record)
        self.save()
        return record

    def execute(self, binary: Path, arguments: list[str], name: str, stdin: str | None = None) -> str:
        for spec in [self.identity["canary"], *self.identity["workloads"]]:
            if str(binary) == spec["executable"] and sha256(binary) != spec["sha256"]:
                raise InvalidResult("executable changed during collection; use a fresh run")
        record = self.event("process", name=name, executable=str(binary), status="started")
        log = self.output / f"{record['id']:05d}-{name}.txt"
        record["log"] = log.name
        self.save()
        started = time.perf_counter()
        process = None
        try:
            with log.open("w", encoding="utf-8") as stream:
                process = subprocess.Popen([str(binary), *arguments], stdin=subprocess.PIPE,
                                           stdout=stream, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
                try:
                    process.communicate(stdin, timeout=self.args.timeout)
                except BaseException:
                    process.kill()
                    process.wait()
                    raise
            record.update(status="ok" if process.returncode == 0 else "failed", returncode=process.returncode)
            if process.returncode:
                raise subprocess.CalledProcessError(process.returncode, process.args)
            return log.read_text(encoding="utf-8", errors="replace")
        except BaseException as error:
            record.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                          error=str(error), error_type=type(error).__name__)
            raise
        finally:
            record["wall_seconds"] = time.perf_counter() - started
            self.save()

    def search(self, binary: Path, nodes: int, name: str) -> dict[str, int]:
        commands = (f"setoption name Threads value 1\nsetoption name Hash value 8\n"
                    f"bench {self.identity['depth']}\nquit\n")
        return parse_search(self.execute(binary, [], name, commands), self.identity["depth"], nodes)

    def canary(self, name: str) -> dict[str, int]:
        spec = self.identity["canary"]
        time.sleep(self.args.cooldown)
        return self.search(Path(spec["executable"]), spec["expected_nodes"], name)

    def acceptable(self, sample: dict[str, int]) -> bool:
        return abs(drift_percent(sample["nps"], self.state["baseline"]["nps"])) <= self.args.drift_percent

    def calibrate(self) -> None:
        for attempt in range(self.args.retries + 1):
            try:
                self.canary("canary-warmup")
                samples = [self.canary("canary-calibration") for _ in range(self.args.canary_samples)]
                median = statistics.median(sample["nps"] for sample in samples)
                rates = [sample["nps"] for sample in samples]
                span = (max(rates) - min(rates)) / median * 100
                stable = span <= self.args.drift_percent
                if self.state.get("baseline"):
                    stable = stable and all(self.acceptable(sample) for sample in samples)
                self.event("calibration", attempt=attempt + 1, samples=samples, span_percent=span, accepted=stable)
                if stable:
                    if not self.state.get("baseline"):
                        self.state["baseline"] = {"nps": median, "samples": samples, "established_at": now()}
                    self.save()
                    print(f"Canary baseline {self.state['baseline']['nps']:,.0f} NPS; "
                          f"calibration span {span:.2f}%.", flush=True)
                    return
            except (OSError, subprocess.SubprocessError) as error:
                self.event("calibration_failure", attempt=attempt + 1, error=str(error))
            if attempt < self.args.retries:
                time.sleep(self.args.retry_delay)
        raise UnstableMachine("canary calibration failed or drifted; cool/idle the machine and resume")

    def warmups(self, workloads: list[dict[str, Any]]) -> None:
        for repetition in range(self.args.warmups):
            for workload in workloads:
                self.measure(workload, f"warmup-{repetition + 1}-{workload['label']}", warmup=True)

    def payload(self, workload: dict[str, Any], name: str) -> Any:
        binary = Path(workload["executable"])
        if workload["kind"] == "search":
            return self.search(binary, workload["expected_nodes"], name)
        return parse_perft(self.execute(binary, ["--perft", str(ROOT / "test_data/standard.epd")], name),
                           self.identity["perft_counts"])

    def measure(self, workload: dict[str, Any], sample_id: str, warmup: bool = False) -> None:
        for attempt in range(self.args.retries + 1):
            try:
                before = self.canary(f"{sample_id}-before")
                if not self.acceptable(before):
                    self.event("sample_attempt", sample_id=sample_id, attempt=attempt + 1,
                               accepted=False, reason="pre_canary_drift", before=before,
                               before_drift_percent=drift_percent(before["nps"], self.state["baseline"]["nps"]))
                else:
                    time.sleep(self.args.cooldown)
                    payload = self.payload(workload, sample_id)
                    after = self.canary(f"{sample_id}-after")
                    bracket_drift = drift_percent(after["nps"], before["nps"])
                    accepted = self.acceptable(after) and abs(bracket_drift) <= self.args.drift_percent
                    reason = ("ok" if accepted else
                              "post_canary_drift" if not self.acceptable(after) else "bracket_drift")
                    baseline_nps = self.state["baseline"]["nps"]
                    record = self.event("sample_attempt", sample_id=sample_id, attempt=attempt + 1,
                                        accepted=accepted, reason=reason,
                                        before=before, after=after, payload=payload, warmup=warmup,
                                        before_drift_percent=drift_percent(before["nps"], baseline_nps),
                                        after_drift_percent=drift_percent(after["nps"], baseline_nps),
                                        bracket_drift_percent=bracket_drift)
                    if accepted:
                        if not warmup:
                            self.state["accepted"][sample_id] = {"label": workload["label"],
                                "kind": workload["kind"], "payload": payload, "event_id": record["id"]}
                            self.save()
                        print(f"Accepted {sample_id}; canary drift "
                              f"{record['before_drift_percent']:+.2f}% / "
                              f"{record['after_drift_percent']:+.2f}%.", flush=True)
                        return
            except (OSError, subprocess.SubprocessError) as error:
                self.event("sample_attempt", sample_id=sample_id, attempt=attempt + 1,
                           accepted=False, reason="process_failure", error=str(error))
            if attempt < self.args.retries:
                print(f"Retrying {sample_id} after cooldown; prior attempt retained.", flush=True)
                time.sleep(self.args.retry_delay)
        raise UnstableMachine(f"{sample_id} exhausted retries; completed accepted samples are saved")

    def collect(self) -> None:
        self.state["status"] = "running"
        self.event("session_start")
        try:
            self.calibrate()
            workloads = self.identity["workloads"]
            self.warmups(workloads)
            for repetition in range(self.args.repeats):
                offset = repetition % len(workloads)
                for workload in workloads[offset:] + workloads[:offset]:
                    sample_id = f"run{repetition + 1}-{workload['label']}"
                    if sample_id not in self.state["accepted"]:
                        self.measure(workload, sample_id)
            self.state.update(status="complete", completed_at=now())
            self.save()
            atomic_json(self.output / "results.json", self.state)
            (self.output / "summary.md").write_text(render_summary(self.state), encoding="utf-8")
            print(f"Saved {self.output / 'results.json'}", flush=True)
        except BaseException as error:
            self.state.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "paused",
                              last_error=str(error), error_type=type(error).__name__)
            self.save()
            raise


def render_summary(state: dict[str, Any]) -> str:
    identity = state["identity"]
    attempts = [event for event in state["events"] if event["kind"] == "sample_attempt"]
    rejected = sum(not event["accepted"] for event in attempts)
    lines = ["# Collected benchmark results", "", f"Source: `{identity['source_commit']}`.", "",
             f"Canary baseline: {state['baseline']['nps']:,.0f} NPS; tolerance: +/-{identity['drift_percent']}%.",
             f"Rejected attempts retained: {rejected}.",
             "Accepted results below exclude warmups and rejected attempts.", "",
             "Canary checks detect relative machine drift, not CPU temperature or an initially slow machine.", ""]
    lines += ["| Sample attempt | Accepted | Before drift % | After drift % | Reason |",
              "|---|---|---:|---:|---|"]
    for attempt in attempts:
        before = attempt.get("before_drift_percent")
        after = attempt.get("after_drift_percent")
        lines.append(f"| {attempt['sample_id']} #{attempt['attempt']} | {attempt['accepted']} | "
                     f"{f'{before:+.2f}' if before is not None else '-'} | "
                     f"{f'{after:+.2f}' if after is not None else '-'} | {attempt['reason']} |")
    lines.append("")
    accepted = list(state["accepted"].values())
    for workload in identity["workloads"]:
        samples = [item["payload"] for item in accepted if item["label"] == workload["label"]]
        lines += [f"## {workload['label']}", ""]
        if workload["kind"] == "search":
            elapsed = summary([sample["elapsed_ms"] for sample in samples])
            nps = summary([sample["nps"] for sample in samples])
            lines += ["| Runs | Nodes | Median ms (min-max) | Median NPS (min-max) |", "|---:|---:|---:|---:|",
                      f"| {len(samples)} | {samples[0]['nodes']:,} | "
                      f"{elapsed['median']:,.0f} ({elapsed['min']:,.0f}-{elapsed['max']:,.0f}) | "
                      f"{nps['median']:,.0f} ({nps['min']:,.0f}-{nps['max']:,.0f}) |", ""]
        else:
            lines += ["| Position | Mode | Nodes | Median seconds (min-max) | Median reported MNPS |",
                      "|---|---|---:|---:|---:|"]
            for index in range(len(samples[0])):
                seconds = summary([sample[index]["seconds"] for sample in samples])
                mnps = statistics.median(sample[index]["reported_mnps"] for sample in samples)
                lines.append(f"| {index // 2 + 1} | {samples[0][index]['mode']} | {samples[0][index]['nodes']:,} | "
                             f"{seconds['median']:.3f} ({seconds['min']:.3f}-{seconds['max']:.3f}) | {mnps:.0f} |")
            lines += ["", "Perft seconds are rounded to three decimals; reported MNPS is truncated.",
                      "Multi perft uses one task per legal root move, not a fixed-size search pool.", ""]
    return "\n".join(lines) + "\n"


def arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("search", "perft", "all"), default="all")
    parser.add_argument("--engine", action="append", default=[], help="label=executable")
    parser.add_argument("--expected-nodes", action="append", default=[], help="label=node-count override")
    parser.add_argument("--perft-engine", type=Path)
    parser.add_argument("--canary", type=Path, required=True, help="fixed reference engine")
    parser.add_argument("--canary-nodes", type=int, help="expected canary nodes; default classical signature")
    parser.add_argument("--canary-reference", type=Path, help="prior results.json or partial.json baseline")
    parser.add_argument("--canary-samples", type=int, default=3)
    parser.add_argument("--drift-percent", type=float, default=5.0)
    parser.add_argument("--cooldown", type=float, default=1.0)
    parser.add_argument("--retry-delay", type=float, default=10.0)
    parser.add_argument("--retries", type=int, default=2, help="extra attempts before pausing")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--environment", type=Path)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args(argv)
    floats = (args.drift_percent, args.cooldown, args.retry_delay, args.timeout)
    if not all(math.isfinite(value) for value in floats):
        parser.error("numeric controls must be finite")
    if (args.repeats < 1 or args.warmups < 0 or args.timeout <= 0 or args.retries < 0 or
            args.canary_samples < 3 or not 0 < args.drift_percent < 100 or min(args.cooldown, args.retry_delay) < 0):
        parser.error("invalid sample counts, drift tolerance, timeout or cooldown")
    args.output = args.output.resolve()
    return args


def make_identity(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    environment = json.loads(args.environment.read_text(encoding="utf-8-sig")) if args.environment else {}
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", "CMakeLists.txt", "src", "app", "tests/cpp"],
                   cwd=ROOT, check=True, capture_output=True)
    signature = dict(re.findall(r"^(DEPTH|NODES|NODES_NNUE)=(\d+)$",
                               (ROOT / "tools/bench_signature.txt").read_text(), re.M))
    overrides = {}
    for entry in args.expected_nodes:
        label, separator, count = entry.partition("=")
        if not separator or not count.isdigit() or int(count) <= 0 or label in overrides:
            raise InvalidResult("expected-nodes must contain unique label=positive-count entries")
        overrides[label] = int(count)
    workloads = []
    labels = set()
    for entry in args.engine if args.mode != "perft" else []:
        label, separator, filename = entry.partition("=")
        if not separator or not re.fullmatch(r"[a-zA-Z0-9_-]+", label) or label in labels or label == "perft":
            raise InvalidResult("each search engine needs a unique filename-safe label=executable")
        binary = Path(filename).resolve(strict=True)
        labels.add(label)
        workloads.append({"label": label, "kind": "search", "executable": str(binary), "sha256": sha256(binary),
                          "expected_nodes": overrides.get(label, int(signature["NODES_NNUE" if "nnue" in label.lower()
                                                                               else "NODES"]))})
    if set(overrides) - labels:
        raise InvalidResult("expected-nodes refers to an unknown search label")
    if args.mode != "perft" and not workloads:
        raise InvalidResult("search requires at least one --engine label=executable")
    if args.mode != "search":
        if args.perft_engine is None:
            raise InvalidResult("perft requires --perft-engine")
        binary = args.perft_engine.resolve(strict=True)
        workloads.append({"label": "perft", "kind": "perft", "executable": str(binary), "sha256": sha256(binary)})
    epd = ROOT / "test_data/standard.epd"
    counts = []
    for line in epd.read_text().splitlines():
        pairs = [(int(depth), int(nodes)) for depth, nodes in re.findall(r";D(\d+) (\d+)", line) if int(depth) <= 5]
        if pairs:
            counts.append(max(pairs)[1])
    if len(counts) != 6:
        raise InvalidResult("expected six committed perft positions")
    canary = args.canary.resolve(strict=True)
    canary_nodes = args.canary_nodes if args.canary_nodes is not None else int(signature["NODES"])
    if canary_nodes <= 0:
        raise InvalidResult("canary expected node count must be positive")
    identity = {"schema": 2, "collector_sha256": sha256(Path(__file__)),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "depth": int(signature["DEPTH"]), "threads": 1, "hash_mb": 8,
        "bench_source_sha256": sha256(ROOT / "src/uci/uci.cpp"), "epd_sha256": sha256(epd),
        "net_sha256": sha256(ROOT / "nets/stk-vector-64.nnue"), "perft_counts": counts,
        "machine": machine_identity(environment), "workloads": workloads,
        "canary": {"executable": str(canary), "sha256": sha256(canary), "expected_nodes": canary_nodes},
        **{key: getattr(args, key) for key in ("repeats", "warmups", "timeout", "drift_percent", "cooldown",
                                             "retry_delay", "retries", "canary_samples")}}
    return identity, environment


def baseline_key(identity: dict[str, Any]) -> dict[str, Any]:
    return {key: identity[key] for key in ("canary", "machine", "depth", "threads", "hash_mb", "bench_source_sha256")}


def validate_state(state: dict[str, Any], identity: dict[str, Any]) -> None:
    baseline = state.get("baseline")
    if baseline is not None and (not math.isfinite(baseline["nps"]) or baseline["nps"] <= 0):
        raise InvalidResult("checkpoint has an invalid canary baseline")
    if state["accepted"] and baseline is None:
        raise InvalidResult("accepted samples have no saved canary baseline")
    planned = {f"run{index + 1}-{workload['label']}": workload
               for index in range(identity["repeats"]) for workload in identity["workloads"]}
    for sample_id, accepted in state["accepted"].items():
        if baseline is None:
            raise InvalidResult("accepted samples have no saved canary baseline")
        if sample_id not in planned or accepted["label"] != planned[sample_id]["label"]:
            raise InvalidResult("checkpoint contains an unknown sample")
        event_id = accepted["event_id"]
        if not isinstance(event_id, int) or not 1 <= event_id <= len(state["events"]):
            raise InvalidResult("checkpoint sample has no acceptance event")
        event = state["events"][event_id - 1]
        if (event.get("kind") != "sample_attempt" or event.get("sample_id") != sample_id or
                event.get("accepted") is not True or event.get("warmup") is not False or
                event.get("payload") != accepted["payload"]):
            raise InvalidResult("checkpoint sample does not match its acceptance event")
        for point in (event["before"], event["after"]):
            if (not math.isfinite(point["nps"]) or point["nps"] <= 0 or
                    abs(drift_percent(point["nps"], baseline["nps"])) > identity["drift_percent"]):
                raise InvalidResult("checkpoint includes a sample outside the saved canary tolerance")
        if abs(drift_percent(event["after"]["nps"], event["before"]["nps"])) > identity["drift_percent"]:
            raise InvalidResult("checkpoint includes excessive drift across a sample bracket")
    if state["status"] == "complete" and set(state["accepted"]) != set(planned):
        raise InvalidResult("complete checkpoint is missing samples")


def load_state(args: argparse.Namespace, identity: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    checkpoint = args.output / "partial.json"
    if args.resume:
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        if state["identity"] != identity:
            raise InvalidResult("resume identity/settings changed; use a fresh output directory")
        validate_state(state, identity)
        if args.canary_reference:
            raise InvalidResult("resume uses its saved canary baseline; omit --canary-reference")
        return state
    if any(path.name != "run.lock" for path in args.output.iterdir()):
        raise InvalidResult("output directory is not empty; use --resume or a fresh directory")
    state = {"identity": identity, "environment": environment, "started_at": now(),
             "status": "new", "events": [], "accepted": {}, "baseline": None}
    if args.canary_reference:
        reference = json.loads(args.canary_reference.read_text(encoding="utf-8"))
        if baseline_key(reference["identity"]) != baseline_key(identity) or not reference.get("baseline"):
            raise InvalidResult("canary reference machine/binary/workload differs or has no baseline")
        baseline = reference["baseline"]
        if not math.isfinite(baseline["nps"]) or baseline["nps"] <= 0:
            raise InvalidResult("canary reference has an invalid baseline")
        state["baseline"] = baseline
        state["reference_sha256"] = sha256(args.canary_reference)
    return state


def main(argv: list[str] | None = None) -> int:
    args = arguments(argv)
    try:
        identity, environment = make_identity(args)
        args.output.mkdir(parents=True, exist_ok=True)
        with run_lock(args.output):
            state = load_state(args, identity, environment)
            if state["status"] == "complete":
                atomic_json(args.output / "results.json", state)
                (args.output / "summary.md").write_text(render_summary(state), encoding="utf-8")
                print("Run already complete; restored results and summary without launching engines.")
            else:
                Collector(args, identity, state).collect()
        return 0
    except KeyboardInterrupt:
        print(f"Interrupted; resume with the same settings and --output {args.output} --resume", flush=True)
        return 130
    except RunBusy as error:
        print(str(error), flush=True)
        return 3
    except (OSError, subprocess.SubprocessError, UnstableMachine, KeyError, TypeError, ValueError) as error:
        print(f"Benchmark stopped: {error}. Inspect {args.output} before resuming.", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
