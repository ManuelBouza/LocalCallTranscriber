[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'El build desacoplado sólo está soportado en Windows.'
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$worker = Join-Path $repositoryRoot 'scripts\package_build_worker.ps1'
$stateDirectory = Join-Path $repositoryRoot 'build\package-build'
$statusPath = Join-Path $stateDirectory 'build-status.json'
$logPath = Join-Path $stateDirectory 'build.log'

if (-not (Test-Path -LiteralPath $worker -PathType Leaf)) {
    throw "No se encontró el worker de build: $worker"
}

if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
    $previous = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
    if ($previous.state -eq 'RUNNING' -and $previous.pid) {
        $existing = Get-Process -Id ([int]$previous.pid) -ErrorAction SilentlyContinue
        if ($null -ne $existing) {
            throw "Ya existe un package build RUNNING con PID $($previous.pid)."
        }
    }
}

New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
Remove-Item -LiteralPath $statusPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $logPath -Force -ErrorAction SilentlyContinue

$powershell = (Get-Command powershell.exe -ErrorAction Stop).Source
$argumentList = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', ('"' + $worker + '"'),
    '-StatusPath', ('"' + $statusPath + '"'),
    '-LogPath', ('"' + $logPath + '"')
)
$process = Start-Process -FilePath $powershell -ArgumentList $argumentList -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(5)
while (-not (Test-Path -LiteralPath $statusPath -PathType Leaf) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 100
}

Write-Host "BUILD_STARTED PID=$($process.Id)"
Write-Host "Status: $statusPath"
Write-Host "Log:    $logPath"
Write-Host 'Consulta: .\scripts\package_build_status.ps1'
Write-Host 'No esperes aquí a que termine el build.'
