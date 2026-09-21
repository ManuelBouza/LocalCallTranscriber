[CmdletBinding()]
param(
    [int]$Tail = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$stateDirectory = Join-Path $repositoryRoot 'build\package-build'
$statusPath = Join-Path $stateDirectory 'build-status.json'

if (-not (Test-Path -LiteralPath $statusPath -PathType Leaf)) {
    Write-Host 'BUILD_STATE_UNKNOWN'
    Write-Host "No existe: $statusPath"
    exit 2
}

$status = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
$effectiveState = [string]$status.state
if ($effectiveState -eq 'RUNNING' -and $status.pid) {
    $process = Get-Process -Id ([int]$status.pid) -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        $effectiveState = 'BUILD_STATE_UNKNOWN'
    }
}

switch ($effectiveState) {
    'RUNNING' { Write-Host 'BUILD_PROCESS_RUNNING' }
    'SUCCESS' { Write-Host 'BUILD_SUCCESS' }
    'FAILED' { Write-Host 'BUILD_FAILED' }
    default { Write-Host 'BUILD_STATE_UNKNOWN' }
}

Write-Host "State:      $effectiveState"
Write-Host "PID:        $($status.pid)"
Write-Host "Started:    $($status.started_at)"
Write-Host "Finished:   $($status.finished_at)"
Write-Host "Exit code:  $($status.exit_code)"
Write-Host "Status:     $statusPath"
Write-Host "Log:        $($status.log)"
Write-Host "Manifest:   $($status.manifest)"
if ($status.error) {
    Write-Host "Error:      $($status.error)"
}

if ($Tail -gt 0 -and (Test-Path -LiteralPath $status.log -PathType Leaf)) {
    Write-Host ''
    Write-Host "--- Últimas $Tail líneas del log ---"
    Get-Content -LiteralPath $status.log -Tail $Tail
}

switch ($effectiveState) {
    'SUCCESS' { exit 0 }
    'RUNNING' { exit 0 }
    'FAILED' { exit 1 }
    default { exit 2 }
}
