[CmdletBinding()]
param(
    [string]$PythonExecutable,
    [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repositoryRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'
$requirementsFile = Join-Path $repositoryRoot 'requirements-dev.txt'

function Get-DefaultPythonExecutable {
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    }
    if ($null -ne $pythonCommand) {
        return $pythonCommand.Source
    }

    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -eq $pyLauncher) {
        $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    }
    if ($null -ne $pyLauncher) {
        $discovered = & $pyLauncher.Source -3 -c 'import sys; print(sys.executable)'
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($discovered)) {
            return $discovered.ToString().Trim()
        }
    }

    throw 'No se encontró Python. Instala Python 3.11 o superior o usa -PythonExecutable <ruta>.'
}

if ([string]::IsNullOrWhiteSpace($PythonExecutable)) {
    $PythonExecutable = Get-DefaultPythonExecutable
}
if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
    throw "El ejecutable Python indicado no existe: $PythonExecutable"
}

$versionText = & $PythonExecutable -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo consultar la versión de Python: $PythonExecutable"
}
$version = [Version]$versionText.ToString().Trim()
if ($version.Major -ne 3 -or $version.Minor -lt 11) {
    throw "Python $version no es compatible. Se requiere Python 3.11 o superior."
}

if (-not (Test-Path -LiteralPath $venvPath)) {
    Write-Host "Creando .venv con Python $version..." -ForegroundColor Cyan
    & $PythonExecutable -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo crear .venv.'
    }
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    throw '.venv existe pero no contiene Scripts\python.exe. Elimina o repara manualmente ese entorno antes de reintentar.'
}

$venvVersionText = & $venvPython -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'
if ($LASTEXITCODE -ne 0) {
    throw 'No se pudo ejecutar el Python de .venv.'
}
$venvVersion = [Version]$venvVersionText.ToString().Trim()
if ($venvVersion.Major -ne 3 -or $venvVersion.Minor -lt 11) {
    throw ".venv usa Python $venvVersion, incompatible con el mínimo 3.11."
}

& $venvPython -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Inicializando pip dentro de .venv...' -ForegroundColor Cyan
    & $venvPython -m ensurepip --upgrade --default-pip
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo inicializar pip dentro de .venv.'
    }
}

if (-not $SkipInstall) {
    if (-not (Test-Path -LiteralPath $requirementsFile -PathType Leaf)) {
        throw "No se encontró el archivo de herramientas de desarrollo: $requirementsFile"
    }

    Write-Host 'Instalando herramientas de desarrollo fijadas dentro de .venv...' -ForegroundColor Cyan
    & $venvPython -m pip install --requirement $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudieron instalar las herramientas de desarrollo en .venv.'
    }

    & $venvPython -m pip install --editable $repositoryRoot --no-build-isolation
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo instalar el paquete local en modo editable dentro de .venv.'
    }
}

& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) {
    throw 'pip check detectó dependencias incompatibles en .venv.'
}

Write-Host ".venv preparada con Python $venvVersion." -ForegroundColor Green
Write-Host 'Ejecuta .\scripts\test.ps1 para pruebas, lint y smoke test en CPU.' -ForegroundColor Green
