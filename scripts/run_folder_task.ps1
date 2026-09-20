[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputDirectory,
    [Parameter(Mandatory)][string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'No se encontró .venv.' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$log = Join-Path $OutputDirectory 'automation.log'
& $python -m local_call_transcriber $InputDirectory --output-dir $OutputDirectory *>> $log
exit $LASTEXITCODE
