"""Legacy launchers must retain caller paths and package entry points."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("command", [
    "tools/benchmark.py", "tools/benchmark_matrix.py",
    "tools/bench/benchmark.py", "tools/bench/benchmark_matrix.py",
    "tools/nnue/build_stk_data.py", "tools/nnue/check_vector64.py",
])
def test_file_command_works_outside_repository(command, tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / command), "--help"],
                            cwd=tmp_path, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
    assert "_entrypoint.py" not in result.stdout


def test_legacy_training_launcher_works_outside_repository(tmp_path):
    if importlib.util.find_spec("torch") is None:
        pytest.skip("training launcher requires PyTorch")
    result = subprocess.run([sys.executable, str(ROOT / "tools/run_pipeline.py"), "--help"],
                            cwd=tmp_path, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "--workdir" in result.stdout


def test_network_checker_keeps_relative_input_path(tmp_path):
    from tools.nnue.contracts import BUCKETS, FEATURES, HEADER, MAGIC, net_layout

    with (tmp_path / "candidate.nnue").open("wb") as stream:
        stream.write(HEADER.pack(MAGIC, 1, FEATURES, 128, BUCKETS))
        stream.truncate(net_layout(128)[1])
    result = subprocess.run([sys.executable, str(ROOT / "tools/nnue/check_vector64.py"), "candidate.nnue"],
                            cwd=tmp_path, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "[PASS] STK-HalfKA 128" in result.stdout


@pytest.mark.parametrize("module", [
    "tools.bench.benchmark", "tools.bench.benchmark_matrix", "tools.nnue.check_vector64",
])
def test_package_command(module):
    result = subprocess.run([sys.executable, "-m", module, "--help"],
                            cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_powershell_launcher_preserves_failure_status(tmp_path):
    powershell = shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is not installed")
    result = subprocess.run([
        powershell, "-NoProfile", "-File", str(ROOT / "tools/sprt_pending.ps1"),
        "-Arbiter", str(tmp_path / "missing-validator"),
    ], cwd=tmp_path, text=True, capture_output=True, timeout=30)
    assert result.returncode != 0
    assert "validator not found" in result.stderr
