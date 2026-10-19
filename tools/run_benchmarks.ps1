[CmdletBinding()]
param(
    [ValidateSet('All', 'Search', 'Perft')]
    [string]$Mode = 'All',
    [switch]$Matrix,
    [int[]]$Depths = @(8, 10, 12, 13, 14, 16),
    [int[]]$ThreadCounts = @(),
    [int[]]$HashSizes = @(8, 64, 256),
    [int[]]$MultiPV = @(1, 3, 5),
    [ValidateSet('Focused', 'Full')]
    [string]$Sweep = 'Focused',
    [switch]$Plan,
    [string]$BuildDir = 'build-benchmark',
    [string]$Classical = '',
    [string]$Nnue = '',
    [string]$ReleasedNnue = '',
    [string]$Canary = '',
    [ValidateRange(0, 2147483647)]
    [int]$CanaryNodes = 0,
    [string]$CanaryReference = '',
    [ValidateRange(3, 100)]
    [int]$CanarySamples = 3,
    [ValidateRange(0.01, 99)]
    [double]$DriftPercent = 5,
    [ValidateRange(0, 3600)]
    [double]$CooldownSeconds = 1,
    [ValidateRange(0, 3600)]
    [double]$RetryDelaySeconds = 10,
    [ValidateRange(0, 100)]
    [int]$Retries = 2,
    [switch]$Resume,
    [string]$Output = '',
    [ValidateRange(1, 1000)]
    [int]$Repeats = 5,
    [ValidateRange(0, 100)]
    [int]$Warmups = 1,
    [ValidateRange(1, 86400)]
    [int]$TimeoutSeconds = 300,
    [string]$Notes = '',
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
function Resolve-RepositoryPath([string]$Value) {
    if (-not [System.IO.Path]::IsPathRooted($Value)) {
        $Value = Join-Path $repoRoot $Value
    }
    return [System.IO.Path]::GetFullPath($Value)
}
Push-Location -LiteralPath $repoRoot
try {
    if ($Plan -and -not $Matrix) { throw '-Plan requires -Matrix.' }
    if (-not $Matrix -and ($PSBoundParameters.ContainsKey('Depths') -or
        $PSBoundParameters.ContainsKey('ThreadCounts') -or $PSBoundParameters.ContainsKey('HashSizes') -or
        $PSBoundParameters.ContainsKey('MultiPV') -or $PSBoundParameters.ContainsKey('Sweep'))) {
        throw 'Depths, ThreadCounts, HashSizes, MultiPV and Sweep require -Matrix.'
    }
    $BuildDir = Resolve-RepositoryPath $BuildDir
    if (-not $Output) {
        if ($Resume) { throw '-Resume requires the original -Output directory.' }
        $Output = Join-Path 'artifacts/benchmarks' (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
    }
    $Output = Resolve-RepositoryPath $Output
    $archive = $Output + '.zip'
    if (-not $Resume -and ((Test-Path -LiteralPath $Output) -or (Test-Path -LiteralPath $archive))) {
        throw 'Output or archive already exists. Choose a new -Output path.'
    }
    if (-not $Classical) {
        $Classical = Join-Path $BuildDir 'bin/ChessEngine.exe'
        if (-not (Test-Path -LiteralPath $Classical)) {
            $Classical = Join-Path $BuildDir 'bin/Release/ChessEngine.exe'
        }
    }
    if (-not $Nnue) {
        $Nnue = Join-Path $BuildDir 'bin/ChessEngine-nnue.exe'
        if (-not (Test-Path -LiteralPath $Nnue)) {
            $Nnue = Join-Path $BuildDir 'bin/Release/ChessEngine-nnue.exe'
        }
    }
    $collectorFile = if ($Matrix) { 'benchmark_matrix.py' } else { 'benchmark.py' }
    $collectorArgs = @(
        (Join-Path $PSScriptRoot $collectorFile), '--mode', $Mode.ToLowerInvariant(),
        '--output', $Output, '--repeats', "$Repeats", '--warmups', "$Warmups",
        '--timeout', "$TimeoutSeconds", '--canary-samples', "$CanarySamples",
        '--drift-percent', $DriftPercent.ToString([System.Globalization.CultureInfo]::InvariantCulture),
        '--cooldown', $CooldownSeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture),
        '--retry-delay', $RetryDelaySeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture),
        '--retries', "$Retries"
    )
    if ($Matrix) {
        $collectorArgs += @('--depths', ($Depths -join ','), '--hash-sizes', ($HashSizes -join ','),
            '--multipv', ($MultiPV -join ','))
        if ($ThreadCounts.Count -gt 0) { $collectorArgs += @('--threads', ($ThreadCounts -join ',')) }
        if ($Sweep -eq 'Full') { $collectorArgs += '--full-matrix' }
        if ($Plan) { $collectorArgs += '--plan' }
    }
    if (-not $Canary) { $Canary = $Classical }
    $canaryPath = (Resolve-Path -LiteralPath $Canary).Path
    $collectorArgs += @('--canary', $canaryPath)
    if ($CanaryNodes -gt 0) { $collectorArgs += @('--canary-nodes', "$CanaryNodes") }
    if ($CanaryReference) {
        $collectorArgs += @('--canary-reference', (Resolve-Path -LiteralPath $CanaryReference).Path)
    }
    if ($Resume) { $collectorArgs += '--resume' }
    if ($Mode -ne 'Perft') {
        $classicalPath = (Resolve-Path -LiteralPath $Classical).Path
        $nnuePath = (Resolve-Path -LiteralPath $Nnue).Path
        $collectorArgs += @('--engine', "classical=$classicalPath", '--engine', "nnue=$nnuePath")
        if ($ReleasedNnue) {
            $releasePath = (Resolve-Path -LiteralPath $ReleasedNnue).Path
            $collectorArgs += @('--engine', "released-nnue=$releasePath")
        }
    }
    if ($Mode -ne 'Search') {
        $perftPath = (Resolve-Path -LiteralPath $Classical).Path
        $collectorArgs += @('--perft-engine', $perftPath)
    }
    $environment = [ordered]@{
        captured_at = (Get-Date).ToString('o')
        timezone = [System.TimeZoneInfo]::Local.Id
        notes = $Notes
        logical_processors = [Environment]::ProcessorCount
        cpu_affinity_pinned = $false
        thermal_power_background_conditions = 'User-managed; record conditions in -Notes'
        build_directory = [System.IO.Path]::GetFullPath($BuildDir)
    }
    try {
        $environment['cpu'] = @(Get-CimInstance Win32_Processor |
            Select-Object Name, NumberOfCores, NumberOfLogicalProcessors)
        $environment['os'] = Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version
    } catch {
        $environment['machine_metadata_error'] = $_.Exception.Message
    }
    $cache = Join-Path $BuildDir 'CMakeCache.txt'
    if (Test-Path -LiteralPath $cache) {
        $environment['cmake_settings'] = @(Get-Content -LiteralPath $cache | Where-Object {
            $_ -match '^(CMAKE_(BUILD_TYPE|CXX_COMPILER|CXX_FLAGS[^:]*|GENERATOR)|ENGINE_[^:]+|OPT_KING_DANGER|EMBED_NNUE):'
        })
    }
    $flags = Join-Path $BuildDir 'CMakeFiles/chess_core.dir/flags.make'
    if (Test-Path -LiteralPath $flags) {
        $environment['compile_flags'] = @(Get-Content -LiteralPath $flags |
            Where-Object { $_ -match '^CXX_(FLAGS|DEFINES) =' })
    }
    $buildEnvironment = [Environment]::GetEnvironmentVariable('CXX')
    $environment['CXX_environment'] = $buildEnvironment
    $metadataFile = Join-Path ([System.IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString() + '-benchmark.json')
    try {
        $environment | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $metadataFile -Encoding UTF8
        $collectorArgs += @('--environment', $metadataFile)
        & $Python @collectorArgs
        $collectorExit = $LASTEXITCODE
    } finally {
        Remove-Item -LiteralPath $metadataFile -ErrorAction SilentlyContinue
    }
    if ($Plan) {
        if ($collectorExit -ne 0) { throw "Matrix preview failed (exit $collectorExit)." }
        return
    }
    if ($collectorExit -ne 3 -and (Test-Path -LiteralPath (Join-Path $Output 'partial.json'))) {
        Compress-Archive -LiteralPath $Output -DestinationPath $archive -Force
    }
    if ($collectorExit -ne 0) {
        throw "Benchmark paused or failed (exit $collectorExit). Logs/checkpoint: $Output. Use -Resume with the same settings."
    }
    Write-Output "Share this archive: $archive"
    Get-Content -LiteralPath (Join-Path $Output 'summary.md')
} finally {
    Pop-Location
}
