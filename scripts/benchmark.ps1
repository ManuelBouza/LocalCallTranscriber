[CmdletBinding()]
param(
    [string]$Output = (Join-Path $env:LOCALAPPDATA 'LocalCallTranscriber\benchmarks\phase-5.json')
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$cache = Join-Path $env:LOCALAPPDATA 'LocalCallTranscriber\models'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'No se encontró .venv. Ejecuta .\scripts\bootstrap.ps1 antes del benchmark.'
}

& $python (Join-Path $PSScriptRoot 'benchmark.py') --output $Output --model-cache $cache
if ($LASTEXITCODE -ne 0) {
    throw "El benchmark falló con código $LASTEXITCODE."
}
