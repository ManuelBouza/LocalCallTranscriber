[CmdletBinding()]
param(
    [string]$PythonExecutable,
    [switch]$SkipInstall,
    [switch]$WithGui
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repositoryRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'
$requirementsFile = Join-Path $repositoryRoot 'requirements-dev.txt'
$guiRequirementsFile = Join-Path $repositoryRoot 'requirements-gui.txt'
$validatedPythonMajor = 3
$validatedPythonMinor = 11

function Get-DefaultPythonExecutable {
    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -eq $pyLauncher) {
        $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    }
    if ($null -eq $pyLauncher) {
        throw 'No se encontró el launcher de Python para Windows (py). Instala CPython 3.11.x y asegúrate de registrar py.'
    }

    $discovered = & $pyLauncher.Source '-3.11' -c 'import sys; print(sys.executable)'
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($discovered)) {
        return $discovered.ToString().Trim()
    }

    throw 'No se encontró CPython 3.11.x. Instálalo con "py install 3.11" o mediante el instalador oficial y vuelve a ejecutar el bootstrap.'
}

$isExplicitOverride = -not [string]::IsNullOrWhiteSpace($PythonExecutable)
if (-not $isExplicitOverride) {
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
if (-not $isExplicitOverride -and ($version.Major -ne $validatedPythonMajor -or $version.Minor -ne $validatedPythonMinor)) {
    throw "El bootstrap normal requiere CPython $validatedPythonMajor.$validatedPythonMinor.x; se detectó Python $version."
}
if ($isExplicitOverride -and ($version.Major -ne $validatedPythonMajor -or $version.Minor -ne $validatedPythonMinor)) {
    Write-Warning "Python $version es una anulación explícita. El baseline validado del MVP es CPython $validatedPythonMajor.$validatedPythonMinor.x; no uses este entorno para la ruta normal de pruebas."
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
if ($venvVersion.Major -ne $version.Major -or $venvVersion.Minor -ne $version.Minor) {
    throw ".venv usa Python $venvVersion, pero el intérprete solicitado usa Python $version. Elimina .venv y ejecuta de nuevo el bootstrap para recrearlo con el intérprete correcto."
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

    if ($WithGui) {
        if (-not (Test-Path -LiteralPath $guiRequirementsFile -PathType Leaf)) {
            throw "No se encontró el archivo de dependencias GUI: $guiRequirementsFile"
        }
        Write-Host 'Instalando dependencias GUI opcionales dentro de .venv...' -ForegroundColor Cyan
        & $venvPython -m pip install --requirement $guiRequirementsFile
        if ($LASTEXITCODE -ne 0) {
            throw 'No se pudieron instalar las dependencias GUI opcionales en .venv.'
        }
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
