# Compatibility launcher; implementation is in tools/experiments/.
param(
  [ValidateSet("A", "B")] [string]$Test = "A",
  [int]$Nodes = 25000,
  [int]$Games = 6000,
  [int]$Conc  = 2,
  [string]$Variant = "crazyhouse",
  # Tests A and B share the qdepth=2 build. Running both at once would have
  # two cmake invocations writing the same directory, so pre-build the three
  # trees once and pass -SkipBuild to both runs.
  [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot "experiments/sprt_dropchecks.ps1") @PSBoundParameters
exit $LASTEXITCODE
