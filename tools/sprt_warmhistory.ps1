# Compatibility launcher; implementation is in tools/experiments/.
param(
  [int]$Nodes = 25000,
  [int]$Games = 6000,
  [int]$Conc  = 10,
  [string]$Engine = "build-bench\bin\ChessEngine-nnue.exe",
  [Parameter(Mandatory=$true)][string]$Arbiter

)

$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot "experiments/sprt_warmhistory.ps1") @PSBoundParameters
exit $LASTEXITCODE
