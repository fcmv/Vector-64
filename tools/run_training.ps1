param(
  [Parameter(Mandatory=$true)][string]$Data,
  [string]$Workdir = "runs\training",
  [string]$Engine = "build\bin\ChessEngine.exe",
  [int]$Epochs = 20,
  [int]$BatchSize = 4096,
  [ValidateSet(128, 1024)][int]$Hidden = 1024,
  [string]$Device = "cuda",
  [string]$Init = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$trainArgs = @(
  (Join-Path $root "tools\nnue\make_net.py"),
  "--workdir", $Workdir, "--engine", $Engine,
  "--epochs", $Epochs, "--batch-size", $BatchSize,
  "--hidden", $Hidden, "--device", $Device
)
if (Test-Path -LiteralPath (Join-Path $Data "manifest.json")) {
  $trainArgs += "--data-dir", $Data
} elseif ((Split-Path $Data -Leaf) -eq "manifest.json") {
  $trainArgs += "--data-dir", (Split-Path $Data -Parent)
} else {
  $trainArgs += "--input", $Data
}
if ($Init) { $trainArgs += "--init", $Init }
python @trainArgs
exit $LASTEXITCODE
