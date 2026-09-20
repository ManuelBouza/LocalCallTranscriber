[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$KeepDeploymentFiles,
    [switch]$SkipPackageSmoke
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$deployTool = Join-Path $repositoryRoot '.venv\Scripts\pyside6-deploy.exe'
$specFile = Join-Path $repositoryRoot 'pysidedeploy.spec'
$distDir = Join-Path $repositoryRoot 'dist'
$expectedVersion = '0.2.0'
$originalCIncludePath = $env:C_INCLUDE_PATH

if ($env:OS -ne 'Windows_NT') {
    throw 'El paquete de release se construye únicamente en Windows.'
}
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    throw 'No se encontró .venv. Ejecuta .\scripts\bootstrap.ps1 -WithGui.'
}
if (-not (Test-Path -LiteralPath $deployTool -PathType Leaf)) {
    throw 'No se encontró pyside6-deploy. Ejecuta .\scripts\bootstrap.ps1 -WithGui.'
}
if (-not (Test-Path -LiteralPath $specFile -PathType Leaf)) {
    throw "No se encontró la configuración de deploy: $specFile"
}
$originalSpecBytes = [IO.File]::ReadAllBytes($specFile)

$installedVersion = & $venvPython -c 'import importlib.metadata; print(importlib.metadata.version("local-call-transcriber"))'
if ($LASTEXITCODE -ne 0 -or $installedVersion.ToString().Trim() -ne $expectedVersion) {
    throw "La .venv no contiene LocalCallTranscriber $expectedVersion. Ejecuta .\scripts\bootstrap.ps1 -WithGui después de sincronizar el repositorio."
}

$qtVersion = & $venvPython -c 'import PySide6; print(PySide6.__version__)'
if ($LASTEXITCODE -ne 0 -or $qtVersion.ToString().Trim() -ne '6.8.3') {
    throw 'La ruta de release requiere PySide6 6.8.3.'
}

if ($null -eq (Get-Command dumpbin.exe -ErrorAction SilentlyContinue)) {
    Write-Warning 'dumpbin.exe no está en PATH. Qt recomienda MSVC/dumpbin para analizar eficientemente dependencias en Windows.'
}

Push-Location $repositoryRoot
try {
    if (-not $DryRun -and (Test-Path -LiteralPath $distDir)) {
        Remove-Item -LiteralPath $distDir -Recurse -Force
    }

    if (-not $DryRun) {
        # Nuitka descarga su MinGW64 compatible cuando no hay MSVC. En esta
        # versión del toolchain, las rutas -I que genera Nuitka requieren
        # volver a exponer sus cabeceras como ruta de sistema para resolver
        # _mingw_stdarg.h.
        & $venvPython -m pip install 'nuitka==2.6.8' 'ordered_set' 'zstandard'
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudieron preparar las dependencias de build de Nuitka (código $LASTEXITCODE)."
        }
        $mingwGcc = & $venvPython -c 'from nuitka.utils.Download import getCachedDownloadedMinGW64; print(getCachedDownloadedMinGW64("x86_64", True, True))'
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo preparar el compilador MinGW64 de Nuitka (código $LASTEXITCODE)."
        }
        $mingwRoot = Split-Path -Parent (Split-Path -Parent $mingwGcc.ToString().Trim())
        $mingwInclude = Join-Path $mingwRoot 'x86_64-w64-mingw32\include'
        if (-not (Test-Path -LiteralPath $mingwInclude -PathType Container)) {
            throw "No se encontró el directorio de cabeceras MinGW64 de Nuitka: $mingwInclude"
        }
        $env:C_INCLUDE_PATH = $mingwInclude
    }

    $deployArguments = @(
        '-c', $specFile,
        '--name', 'LocalCallTranscriber',
        '-f'
    )
    if ($DryRun) {
        $deployArguments += '--dry-run'
    }
    if ($KeepDeploymentFiles) {
        $deployArguments += '--keep-deployment-files'
    }

    & $deployTool @deployArguments
    if ($LASTEXITCODE -ne 0) {
        throw "pyside6-deploy falló con código $LASTEXITCODE."
    }

    if ($DryRun) {
        Write-Host 'PASS: configuración de pyside6-deploy evaluada en modo dry-run.' -ForegroundColor Green
        exit 0
    }

    $executables = @(
        Get-ChildItem -LiteralPath $distDir -Recurse -File -Filter 'LocalCallTranscriber.exe'
    )
    if ($executables.Count -ne 1) {
        throw "Se esperaba exactamente un LocalCallTranscriber.exe en dist; encontrados: $($executables.Count)."
    }
    $executable = $executables[0]

    if (-not $SkipPackageSmoke) {
        & $executable.FullName '--package-smoke'
        if ($LASTEXITCODE -ne 0) {
            throw "El smoke del ejecutable empaquetado falló con código $LASTEXITCODE."
        }
    }

    $forbiddenModelFiles = @(
        Get-ChildItem -LiteralPath $distDir -Recurse -File |
            Where-Object {
                $_.Name -eq 'model.bin' -or
                $_.Extension -in @('.safetensors', '.gguf')
            }
    )
    if ($forbiddenModelFiles.Count -gt 0) {
        throw 'El paquete contiene archivos que parecen pesos de modelos; los modelos deben permanecer fuera del artefacto.'
    }

    $allFiles = @(Get-ChildItem -LiteralPath $distDir -Recurse -File)
    $totalBytes = ($allFiles | Measure-Object -Property Length -Sum).Sum
    $hash = (Get-FileHash -LiteralPath $executable.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $manifest = [ordered]@{
        version = $expectedVersion
        packaging = 'pyside6-deploy'
        mode = 'standalone'
        executable = $executable.FullName.Substring($repositoryRoot.Length + 1)
        executable_sha256 = $hash
        file_count = $allFiles.Count
        total_bytes = $totalBytes
        package_smoke = (-not $SkipPackageSmoke)
    }
    $manifestPath = Join-Path $distDir 'package-manifest.json'
    $manifest | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding utf8

    Write-Host "PASS: paquete Windows generado y validado: $($executable.FullName)" -ForegroundColor Green
    Write-Host "Manifest: $manifestPath" -ForegroundColor Green
}
finally {
    # pyside6-deploy normaliza rutas y reescribe el spec; la configuración
    # versionada debe permanecer portable y el dry-run no debe ensuciar Git.
    [IO.File]::WriteAllBytes($specFile, $originalSpecBytes)
    $env:C_INCLUDE_PATH = $originalCIncludePath
    Pop-Location
}
