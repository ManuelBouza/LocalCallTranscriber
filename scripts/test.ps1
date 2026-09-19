[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    throw 'No se encontró .venv. Ejecuta .\scripts\bootstrap.ps1 antes de las pruebas.'
}

& $venvPython -m pytest
if ($LASTEXITCODE -ne 0) {
    throw 'pytest falló.'
}

& $venvPython -m ruff check src tests
if ($LASTEXITCODE -ne 0) {
    throw 'ruff falló.'
}

& $venvPython -c 'import local_call_transcriber; print("Smoke test del paquete OK")'
if ($LASTEXITCODE -ne 0) {
    throw 'El smoke test del paquete falló.'
}

& (Join-Path $repositoryRoot 'tests\test_doctor.ps1')
if ($LASTEXITCODE -ne 0) {
    throw 'La validación del preflight falló.'
}

Write-Host 'PASS: pruebas, lint, smoke test y preflight completados en CPU.' -ForegroundColor Green
