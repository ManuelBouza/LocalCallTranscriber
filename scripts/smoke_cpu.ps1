[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'No se encontró .venv. Ejecuta .\scripts\bootstrap.ps1 antes del smoke test CPU.'
}

& $python (Join-Path $PSScriptRoot 'smoke_cpu.py')
if ($LASTEXITCODE -ne 0) {
    throw "El smoke test CPU falló con código $LASTEXITCODE."
}
