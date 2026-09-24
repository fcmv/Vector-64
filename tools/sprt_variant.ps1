# SPRT one drop-variant knob against another value of the same knob.
#
#   powershell -ExecutionPolicy Bypass -File tools\sprt_variant.ps1 -Test handmat
#   powershell -ExecutionPolicy Bypass -File tools\sprt_variant.ps1 -Test nullmove
#   powershell -ExecutionPolicy Bypass -File tools\sprt_variant.ps1 -Test drophist
#   powershell -ExecutionPolicy Bypass -File tools\sprt_variant.ps1 -Test dropcheck
#   powershell -ExecutionPolicy Bypass -File tools\sprt_variant.ps1 -Test kingdanger
#   powershell -ExecutionPolicy Bypass -File tools\sprt_variant.ps1 `
#       -Define ENGINE_KING_DANGER_SCALE -New 6 -Base 0     # anything, by hand
#
# Generalises tools/sprt_dropchecks.ps1: every drop-variant knob is a
# compile-time define precisely so that the two sides of a test are two
# binaries built from identical source rather than one binary in two modes.
# This builds both and matches them.
#
# Each side is a single-threaded engine, so -Conc is literally how many cores
# the run uses. Adjudication is by ChessEngine-validator, not a chess library:
# the engine is the only thing here that knows the rules of crazyhouse.
#
# SPRT: H0 elo<=0, H1 elo>=5, alpha=beta=0.05, stops at LLR +/-2.94.

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

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

# Named tests. Each is "does turning this on beat leaving it off", phrased so
# that the new side is the change being proposed.
switch ($Test) {
  "handmat" {
    $Define = "ENGINE_VARIANT_HAND_MATERIAL"; $New = "1"; $Base = "0"
    $label = "reserve material in the evaluation: ON vs OFF"
  }
  "nullmove" {
    $Define = "ENGINE_VARIANT_NULLMOVE"; $New = "0"; $Base = "1"
    $label = "null-move pruning in drop variants: OFF vs ON"
  }
  "drophist" {
    $Define = "ENGINE_VARIANT_DROP_HISTORY"; $New = "1"; $Base = "0"
    $label = "drop history table: ON vs OFF"
  }
  "dropcheck" {
    $Define = "ENGINE_DROP_CHECK_QDEPTH"; $New = "2"; $Base = "0"
    $label = "drop-checks in qsearch: 2 plies vs OFF"
  }
  "kingdanger" {
    $Define = "ENGINE_KING_DANGER_SCALE"; $New = "6"; $Base = "0"
    $label = "drop king-danger term: scale 6 vs OFF"
  }
  default {
    if (-not $Define -or -not $New -or -not $Base) {
      Write-Error "custom test needs -Define, -New and -Base"; exit 1
    }
    $label = "$Define = $New vs $Base"
  }
}

$tag     = ($Define -replace '^ENGINE_', '').ToLower()
$newDir  = Join-Path $root ("build-{0}-{1}" -f $tag, $New)
$baseDir = Join-Path $root ("build-{0}-{1}" -f $tag, $Base)
$logdir  = Join-Path $root "sprt\logs"
New-Item -ItemType Directory -Force -Path $logdir | Out-Null
$log = Join-Path $logdir ("{0}_{1}_{2}v{3}_{4}n.log" -f $tag, $Variant, $New, $Base, $Nodes)

# Inherit the generator the main build tree already uses. Without this a fresh
# directory falls back to the platform default, which on a machine that also
# has Visual Studio installed silently switches toolchain mid-comparison.
function Get-Generator {
  $cache = Join-Path $root "build\CMakeCache.txt"
  if (Test-Path $cache) {
    $line = Select-String -Path $cache -Pattern '^CMAKE_GENERATOR:INTERNAL=(.+)$' |
            Select-Object -First 1
    if ($line) { return $line.Matches[0].Groups[1].Value }
  }
  return $null
}

function Build-Side([string]$dir, [string]$value) {
  Write-Host ("  building {0}={1} -> {2}" -f $Define, $value, (Split-Path $dir -Leaf))
  $gen = Get-Generator
  $genArgs = if ($gen) { @("-G", $gen) } else { @() }
  cmake -S $root -B $dir @genArgs -DCMAKE_BUILD_TYPE=Release -DENGINE_VIZ=OFF `
        "-D$Define=$value" | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "cmake configure failed for $Define=$value" }
  cmake --build $dir --target ChessEngine-variants ChessEngine-validator -j | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "build failed for $Define=$value" }
}

Write-Host ""
Write-Host "===================================================================="
Write-Host "  STK-Vector-64  --  $label"
Write-Host "===================================================================="
if ($SkipBuild) {
  Write-Host "  -SkipBuild: using the existing build trees"
} else {
  Build-Side $newDir  $New
  Build-Side $baseDir $Base
}

$newExe  = Join-Path $newDir  "bin\ChessEngine-variants.exe"
$baseExe = Join-Path $baseDir "bin\ChessEngine-variants.exe"
$arbiter = Join-Path $newDir  "bin\ChessEngine-validator.exe"
foreach ($f in @($newExe, $baseExe, $arbiter)) {
  if (-not (Test-Path $f)) { Write-Error "missing binary: $f"; exit 1 }
}

Write-Host "--------------------------------------------------------------------"
Write-Host ("  new     : {0}={1}" -f $Define, $New)
Write-Host ("  base    : {0}={1}" -f $Define, $Base)
Write-Host ("  variant : {0}   (arbiter: ChessEngine-validator)" -f $Variant)
Write-Host ("  test    : {0} nodes/move  |  up to {1} games  |  {2} workers" -f $Nodes, $Games, $Conc)
Write-Host ("  gate    : H0 elo<=0  H1 elo>=5   (accept at LLR +/-2.94)")
Write-Host ("  log     : {0}" -f $log)
Write-Host "===================================================================="
Write-Host "  Classical eval only -- NNUE is refused in variant mode by design."
Write-Host "--------------------------------------------------------------------"

$sw = [System.Diagnostics.Stopwatch]::StartNew()

python (Join-Path $root "tools\nnue\match.py") `
  --engine $newExe --base-engine $baseExe --arbiter $arbiter `
  --variant $Variant `
  --sprt 0 5 --games $Games --nodes $Nodes `
  --concurrency $Conc --seed 606060 2>&1 | Tee-Object -FilePath $log

$sw.Stop()
Write-Host "--------------------------------------------------------------------"
Write-Host ("  finished in {0:n1} min. Full log: {1}" -f $sw.Elapsed.TotalMinutes, $log)
Write-Host ("  Paste the final: line back; the {0} default gets set from it." -f $Define)
Write-Host "===================================================================="
