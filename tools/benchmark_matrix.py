"""Collect a fixed-depth search matrix using the resumable benchmark canary."""
from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import benchmark as bench


def positive_values(value: str, maximum: int) -> list[int]:
    try:
        values = list(dict.fromkeys(int(part) for part in value.split(",")))
    except ValueError as error:
        raise bench.InvalidResult("matrix values must be comma-separated integers") from error
    if not values or any(number < 1 or number > maximum for number in values):
        raise bench.InvalidResult(f"matrix values must be between 1 and {maximum}")
    return values


def configurations(depths: list[int], threads: list[int], hashes: list[int], multipv: list[int],
                   full: bool) -> list[tuple[int, int, int, int]]:
    if full:
        return list(itertools.product(depths, threads, hashes, multipv))
    baseline = (13, 1, 8, 1)
    candidates = [baseline]
    for axis, values in enumerate((depths, threads, hashes, multipv)):
        for value in values:
            candidate = list(baseline)
            candidate[axis] = value
            candidates.append((candidate[0], candidate[1], candidate[2], candidate[3]))
    return list(dict.fromkeys(candidates))


def arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--depths", default="8,10,12,13,14,16")
    parser.add_argument("--threads", default=",".join(str(n) for n in (1, 2, 4, 8, 12, 16, 32, 64)
                                                     if n <= (os.cpu_count() or 1)))
    parser.add_argument("--hash-sizes", default="8,64,256")
    parser.add_argument("--multipv", default="1,3,5")
    parser.add_argument("--full-matrix", action="store_true")
    parser.add_argument("--plan", action="store_true")
    if argv is None:
        argv = sys.argv[1:]
    if "--help" in argv or "-h" in argv:
        parser.print_help()
        print("\nCommon collector options:")
        bench.arguments(["--help"])
    matrix, remaining = parser.parse_known_args(argv)
    args = bench.arguments(remaining)
    args.matrix = vars(matrix)
    try:
        args.configurations = configurations(
            positive_values(matrix.depths, 246), positive_values(matrix.threads, 64),
            positive_values(matrix.hash_sizes, 4096), positive_values(matrix.multipv, 32), matrix.full_matrix)
    except bench.InvalidResult as error:
        parser.error(str(error))
    return args


def make_identity(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    identity, environment = bench.make_identity(args)
    profiles = [workload for workload in identity["workloads"] if workload["kind"] == "search"]
    workloads = []
    for depth, threads, hash_mb, multipv in args.configurations:
        for profile in profiles:
            workloads.append({**profile, "label": f"{profile['label']}-d{depth}-t{threads}-h{hash_mb}-pv{multipv}",
                              "depth": depth, "threads": threads, "hash_mb": hash_mb, "multipv": multipv})
    workloads += [workload for workload in identity["workloads"] if workload["kind"] == "perft"]
    identity.update(matrix_schema=1, matrix_collector_sha256=bench.sha256(Path(__file__)),
                    engine_profiles=profiles, workloads=workloads,
                    matrix_configurations=[list(row) for row in args.configurations])
    return identity, environment


def parse_matrix_search(stdout: str, workload: dict[str, Any]) -> dict[str, int]:
    matches = bench.BENCH.findall(stdout)
    if len(matches) != 1:
        raise bench.InvalidResult("expected exactly one complete matrix benchmark reply")
    nodes = int(matches[0][1])
    result = bench.parse_search(stdout, workload["depth"], nodes)
    if nodes <= 0:
        raise bench.InvalidResult("matrix search returned no nodes")
    if (workload["depth"], workload["threads"], workload["hash_mb"], workload["multipv"]) == (13, 1, 8, 1):
        if nodes != workload["expected_nodes"]:
            raise bench.InvalidResult("canonical matrix search fingerprint mismatch")
    return result


def validate_matrix_state(state: dict[str, Any], identity: dict[str, Any]) -> None:
    bench.validate_state(state, identity)
    workloads = {workload["label"]: workload for workload in identity["workloads"]}
    for accepted in state["accepted"].values():
        workload = workloads[accepted["label"]]
        if workload["kind"] != "search":
            continue
        payload = accepted["payload"]
        parse_matrix_search(f"bench depth {workload['depth']} nodes {payload['nodes']} "
                            f"time {payload['elapsed_ms']}ms nps {payload['nps']}", workload)
        if workload["threads"] == 1 and state.get("matrix_nodes", {}).get(workload["label"]) != payload["nodes"]:
            raise bench.InvalidResult("checkpoint matrix node consistency mismatch")


def render_summary(state: dict[str, Any]) -> str:
    perft_state = {**state, "identity": {**state["identity"], "workloads": [workload
                  for workload in state["identity"]["workloads"] if workload["kind"] == "perft"]}}
    lines = [bench.render_summary(perft_state), "## Fixed-depth search matrix", "",
             "| Profile | Runs | Nodes median (min-max) | Time ms median (min-max) | NPS median (min-max) |",
             "|---|---:|---:|---:|---:|"]
    for workload in state["identity"]["workloads"]:
        if workload["kind"] != "search":
            continue
        samples = [item["payload"] for item in state["accepted"].values() if item["label"] == workload["label"]]
        columns = []
        for key in ("nodes", "elapsed_ms", "nps"):
            stats = bench.summary([sample[key] for sample in samples])
            columns.append(f"{stats['median']:,.0f} ({stats['min']:,.0f}-{stats['max']:,.0f})")
        lines.append(f"| {workload['label']} | {len(samples)} | " + " | ".join(columns) + " |")
    return ("\n".join(lines) + "\n\n## Matrix interpretation\n\n"
            "Each search label records depth (d), threads (t), hash MB (h) and MultiPV (pv).\n"
            "Search samples use the built-in eight-position suite in a fresh process.\n"
            "The engine clears search state once at suite start; positions share its evolving state.\n"
            "Only d13-t1-h8-pv1 has a committed golden node count. Other single-thread\n"
            "configurations are checked for repeat consistency, which is not independent correctness proof.\n"
            "Threaded node counts can vary; compare time to depth and nodes as well as NPS.\n"
            "These are fixed-depth and perft measurements, not fixed-node/time or Elo tests.\n")


class MatrixCollector(bench.Collector):
    def calibrate(self) -> None:
        for profile in self.identity["engine_profiles"]:
            self.search(Path(profile["executable"]), profile["expected_nodes"],
                        f"signature-{profile['label']}")
        super().calibrate()

    def payload(self, workload: dict[str, Any], name: str) -> Any:
        if workload["kind"] != "search":
            return super().payload(workload, name)
        commands = (f"setoption name Threads value {workload['threads']}\n"
                    f"setoption name Hash value {workload['hash_mb']}\n"
                    f"setoption name MultiPV value {workload['multipv']}\n"
                    f"bench {workload['depth']}\nquit\n")
        output = self.execute(Path(workload["executable"]), [], name, commands)
        if "info string setoption" in output:
            raise bench.InvalidResult("engine rejected a matrix option; inspect the raw transcript")
        payload = parse_matrix_search(output, workload)
        if workload["threads"] == 1:
            fingerprints = self.state.setdefault("matrix_nodes", {})
            prior = fingerprints.setdefault(workload["label"], payload["nodes"])
            if prior != payload["nodes"]:
                raise bench.InvalidResult(f"single-thread nodes changed for {workload['label']}")
            self.save()
        return payload


def main(argv: list[str] | None = None) -> int:
    args = arguments(argv)
    try:
        identity, environment = make_identity(args)
        if args.matrix["plan"]:
            plan = {"workloads": identity["workloads"], "measured_samples": len(identity["workloads"]) * args.repeats,
                    "warmup_samples": len(identity["workloads"]) * args.warmups,
                    "canary_processes_minimum": 1 + args.canary_samples +
                    2 * len(identity["workloads"]) * (args.repeats + args.warmups),
                    "notes": "No engines launched. Extra processes are needed for signature gates and retries."}
            print(json.dumps(plan, indent=2))
            return 0
        args.output.mkdir(parents=True, exist_ok=True)
        with bench.run_lock(args.output):
            state = bench.load_state(args, identity, environment)
            validate_matrix_state(state, identity)
            if state["status"] != "complete":
                MatrixCollector(args, identity, state).collect()
            bench.atomic_json(args.output / "results.json", state)
            (args.output / "summary.md").write_text(render_summary(state), encoding="utf-8")
            print(f"Matrix complete: {args.output / 'summary.md'}", flush=True)
        return 0
    except KeyboardInterrupt:
        print(f"Interrupted; resume with the same settings and --output {args.output} --resume", flush=True)
        return 130
    except bench.RunBusy as error:
        print(str(error), flush=True)
        return 3
    except (OSError, subprocess.SubprocessError, bench.UnstableMachine, KeyError, TypeError, ValueError) as error:
        print(f"Benchmark stopped: {error}. Inspect {args.output} before resuming.", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
