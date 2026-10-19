# Compatibility launcher; implementation is in tools/experiments/.
param(
  [int]$Nodes = 25000,
  [int]$Games = 6000,
  [int]$Conc  = 10,
  [Parameter(Mandatory=$true)][string]$Arbiter

)

$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot "experiments/sprt_conthist.ps1") @PSBoundParameters
exit $LASTEXITCODE
