from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("matrix_mode", [False, True])
def test_wrapper_anchors_paths_to_repo_when_native_cwd_differs(tmp_path, matrix_mode):
    powershell = shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell 7 is needed for the wrapper regression test")
    repo = tmp_path / "repository"
    (repo / "tools").mkdir(parents=True)
    (repo / "build-benchmark").mkdir()
    shutil.copyfile(ROOT / "tools/run_benchmarks.ps1", repo / "tools/run_benchmarks.ps1")
    fixture = tmp_path / "fixture.ps1"
    fixture.write_text(r'''
param([string]$Repository, [string]$PythonExecutable, [string]$NativeDirectory, [string]$MatrixMode)
$ErrorActionPreference = 'Stop'
[Environment]::CurrentDirectory = $NativeDirectory
Set-Location -LiteralPath $Repository
function Invoke-CollectorFixture {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$CollectorArguments)
    $outIndex = [Array]::IndexOf($CollectorArguments, '--output')
    $envIndex = [Array]::IndexOf($CollectorArguments, '--environment')
    $fixtureOutput = $CollectorArguments[$outIndex + 1]
    New-Item -ItemType Directory -Path $fixtureOutput -Force | Out-Null
    Copy-Item -LiteralPath $CollectorArguments[$envIndex + 1] -Destination (Join-Path $fixtureOutput 'environment.json')
    $CollectorArguments | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $fixtureOutput 'arguments.json')
    '{}' | Set-Content -LiteralPath (Join-Path $fixtureOutput 'partial.json')
    'Synthetic output. No engine launched.' | Set-Content -LiteralPath (Join-Path $fixtureOutput 'summary.md')
    $global:LASTEXITCODE = 0
}
$modeArguments = @{}
if ($MatrixMode -eq 'True') {
    $modeArguments = @{
        Matrix = $true; Depths = @(8, 13); ThreadCounts = @(1, 2); HashSizes = @(8, 64); MultiPV = @(1, 3)
    }
}
& ./tools/run_benchmarks.ps1 -Mode All -Output artifacts/controlled-run -Classical $PythonExecutable `
    -Nnue $PythonExecutable -Python Invoke-CollectorFixture @modeArguments
& ./tools/run_benchmarks.ps1 -Mode All -Output artifacts/controlled-run -Classical $PythonExecutable `
    -Nnue $PythonExecutable -Python Invoke-CollectorFixture @modeArguments -Resume
''', encoding="utf-8")
    completed = subprocess.run([powershell, "-NoProfile", "-File", str(fixture), str(repo), sys.executable,
                                str(tmp_path), str(matrix_mode)], capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    output = repo / "artifacts/controlled-run"
    assert output.is_dir()
    assert output.with_suffix(".zip").is_file()
    assert not (tmp_path / "artifacts/controlled-run").exists()
    environment = json.loads((output / "environment.json").read_text(encoding="utf-8-sig"))
    assert Path(environment["build_directory"]) == repo / "build-benchmark"
    arguments = json.loads((output / "arguments.json").read_text(encoding="utf-8-sig"))
    assert arguments[arguments.index("--output") + 1] == str(output)
    assert "--resume" in arguments
    if matrix_mode:
        assert arguments[0].endswith("benchmark_matrix.py")
        for option, value in (("--depths", "8,13"), ("--threads", "1,2"), ("--hash-sizes", "8,64"),
                              ("--multipv", "1,3")):
            assert arguments[arguments.index(option) + 1] == value
    else:
        assert arguments[0].endswith("benchmark.py")
