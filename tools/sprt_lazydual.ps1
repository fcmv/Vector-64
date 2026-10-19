# Compatibility launcher; implementation is in tools/experiments/.
param(
  [int]$LazyMargin     = 500,
  [int]$SmallThreshold = 300,
  [int]$Nodes          = 8000,
  [int]$Games          = 3000,
  [int]$Conc           = 10,
  [Parameter(Mandatory=$true)][string]$Arbiter

)

$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot "experiments/sprt_lazydual.ps1") @PSBoundParameters
exit $LASTEXITCODE
