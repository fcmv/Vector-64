# Compatibility launcher; implementation is in tools/experiments/.
param(
  [ValidateSet("handmat", "nullmove", "drophist", "dropcheck", "kingdanger", "custom")]
  [string]$Test = "custom",
  [string]$Define = "",
  [string]$New = "",
  [string]$Base = "",
  [int]$Nodes = 25000,
  [int]$Games = 6000,
  [int]$Conc  = 4,
  [string]$Variant = "crazyhouse",
  [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot "experiments/sprt_variant.ps1") @PSBoundParameters
exit $LASTEXITCODE
