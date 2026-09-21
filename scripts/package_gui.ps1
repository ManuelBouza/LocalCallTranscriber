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
$smokeWorkspace = Join-Path $repositoryRoot 'build\package-smoke'
$smokeFixtureScript = Join-Path $repositoryRoot 'deploy\create_package_smoke_fixture.py'
$expectedVersion = '0.2.0'
$smokeInputVariable = 'LOCALCALLTRANSCRIBER_PACKAGE_SMOKE_INPUT'
$originalSmokeInput = [Environment]::GetEnvironmentVariable($smokeInputVariable, 'Process')
$originalCIncludePath = $env:C_INCLUDE_PATH

function Invoke-NativeCaptured {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $false)]
        [string[]]$Arguments = @()
    )

    # Windows PowerShell 5.1 turns native stderr into PowerShell ErrorRecords and
    # $ErrorActionPreference='Stop' can abort the script before $LASTEXITCODE is
    # inspected. Keep stderr visible/loggable but decide success from exit code.
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & $FilePath @Arguments
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    [pscustomobject]@{
        Output = @($output)
        ExitCode = $exitCode
    }
}

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
if (-not (Test-Path -LiteralPath $smokeFixtureScript -PathType Leaf)) {
    throw "No se encontró el generador del fixture de package smoke: $smokeFixtureScript"
}
$originalSpecBytes = [IO.File]::ReadAllBytes($specFile)

$versionProbe = Invoke-NativeCaptured -FilePath $venvPython -Arguments @(
    '-c',
    "from importlib.metadata import version; print(version('local-call-transcriber'))"
)
$installedVersion = if ($versionProbe.Output.Count -gt 0) {
    ($versionProbe.Output | Select-Object -Last 1).ToString().Trim()
}
else {
    ''
}
if ($versionProbe.ExitCode -ne 0 -or $installedVersion -ne $expectedVersion) {
    throw "La .venv no contiene LocalCallTranscriber $expectedVersion. Ejecuta .\scripts\bootstrap.ps1 -WithGui después de sincronizar el repositorio."
}

$qtProbe = Invoke-NativeCaptured -FilePath $venvPython -Arguments @(
    '-c',
    'import PySide6; print(PySide6.__version__)'
)
$qtVersion = if ($qtProbe.Output.Count -gt 0) {
    ($qtProbe.Output | Select-Object -Last 1).ToString().Trim()
}
else {
    ''
}
if ($qtProbe.ExitCode -ne 0 -or $qtVersion -ne '6.8.3') {
    throw 'La ruta de release requiere PySide6 6.8.3.'
}

if ($null -eq (Get-Command dumpbin.exe -ErrorAction SilentlyContinue)) {
    Write-Warning 'dumpbin.exe no está en PATH. Qt recomienda MSVC/dumpbin para analizar eficientemente dependencias en Windows.'
}

# pyside6-deploy usa el Nuitka fijado en pysidedeploy.spec. Se prepara
# explícitamente esa misma versión antes de consultar el WinLibs soportado.
$buildDependencyProbe = Invoke-NativeCaptured -FilePath $venvPython -Arguments @(
    '-m', 'pip', 'install',
    'nuitka==4.2.1',
    'ordered_set',
    'zstandard'
)
$buildDependencyProbe.Output | ForEach-Object { Write-Host $_ }
if ($buildDependencyProbe.ExitCode -ne 0) {
    throw "No se pudieron preparar las dependencias de build de Nuitka (código $($buildDependencyProbe.ExitCode))."
}

$mingwProbe = Invoke-NativeCaptured -FilePath $venvPython -Arguments @(
    '-c',
    "from nuitka.utils.Download import getCachedDownloadedMinGW64; print(getCachedDownloadedMinGW64('x86_64', True, True))"
)
if ($mingwProbe.ExitCode -ne 0 -or $mingwProbe.Output.Count -eq 0) {
    throw 'No se pudo resolver el MinGW64 soportado por Nuitka.'
}
$mingwGcc = ($mingwProbe.Output | Select-Object -Last 1).ToString().Trim()
if (-not (Test-Path -LiteralPath $mingwGcc -PathType Leaf)) {
    throw "Nuitka devolvió un gcc.exe inexistente: $mingwGcc"
}

$mingwRoot = Split-Path -Parent (Split-Path -Parent $mingwGcc)
$mingwInclude = Join-Path $mingwRoot 'x86_64-w64-mingw32\include'
$intrinImpl = Join-Path $mingwInclude 'psdk_inc\intrin-impl.h'
if (-not (Test-Path -LiteralPath $intrinImpl -PathType Leaf)) {
    throw "El WinLibs de Nuitka no contiene la cabecera requerida: $intrinImpl"
}

if ([string]::IsNullOrWhiteSpace($originalCIncludePath)) {
    $env:C_INCLUDE_PATH = $mingwInclude
}
else {
    $env:C_INCLUDE_PATH = "$mingwInclude;$originalCIncludePath"
}
Write-Host "MinGW include temporal: $mingwInclude"

Push-Location $repositoryRoot
try {
    if (-not $DryRun -and (Test-Path -LiteralPath $distDir)) {
        Remove-Item -LiteralPath $distDir -Recurse -Force
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

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $deployTool @deployArguments | ForEach-Object { Write-Host $_ }
        $deployExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($deployExitCode -ne 0) {
        throw "pyside6-deploy falló con código $deployExitCode."
    }

    if ($DryRun) {
        Write-Host 'PASS: configuración de pyside6-deploy evaluada en modo dry-run.' -ForegroundColor Green
        return
    }

    $executables = @(
        Get-ChildItem -LiteralPath $distDir -Recurse -File -Filter 'LocalCallTranscriber.exe'
    )
    if ($executables.Count -eq 0) {
        $generatedExecutables = @(
            Get-ChildItem -LiteralPath $distDir -Recurse -File -Filter 'gui_main.exe'
        )
        if ($generatedExecutables.Count -eq 1) {
            $renamedExecutable = Join-Path $generatedExecutables[0].DirectoryName 'LocalCallTranscriber.exe'
            Rename-Item -LiteralPath $generatedExecutables[0].FullName -NewName 'LocalCallTranscriber.exe'
            $executables = @(Get-Item -LiteralPath $renamedExecutable)
        }
    }
    if ($executables.Count -ne 1) {
        throw "Se esperaba exactamente un LocalCallTranscriber.exe en dist; encontrados: $($executables.Count)."
    }
    $executable = $executables[0]

    if (-not $SkipPackageSmoke) {
        if (Test-Path -LiteralPath $smokeWorkspace) {
            Remove-Item -LiteralPath $smokeWorkspace -Recurse -Force
        }
        New-Item -ItemType Directory -Path $smokeWorkspace -Force | Out-Null
        $smokeInput = Join-Path $smokeWorkspace 'smoke.mp4'

        $fixtureProbe = Invoke-NativeCaptured -FilePath $venvPython -Arguments @(
            $smokeFixtureScript,
            $smokeInput
        )
        $fixtureProbe.Output | ForEach-Object { Write-Host $_ }
        if ($fixtureProbe.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $smokeInput -PathType Leaf)) {
            throw 'No se pudo generar el MP4 temporal para el package smoke.'
        }

        [Environment]::SetEnvironmentVariable($smokeInputVariable, $smokeInput, 'Process')
        $smokeStdout = Join-Path $smokeWorkspace 'stdout.txt'
        $smokeStderr = Join-Path $smokeWorkspace 'stderr.txt'
        $smokeProcess = Start-Process `
            -FilePath $executable.FullName `
            -ArgumentList '--package-smoke' `
            -RedirectStandardOutput $smokeStdout `
            -RedirectStandardError $smokeStderr `
            -Wait `
            -PassThru
        if ($smokeProcess.ExitCode -ne 0) {
            if (Test-Path -LiteralPath $smokeStdout -PathType Leaf) {
                Get-Content -LiteralPath $smokeStdout | ForEach-Object { Write-Host $_ }
            }
            if (Test-Path -LiteralPath $smokeStderr -PathType Leaf) {
                Get-Content -LiteralPath $smokeStderr | ForEach-Object { Write-Host $_ }
            }
            throw "El smoke del ejecutable empaquetado falló con código $($smokeProcess.ExitCode)."
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
    [IO.File]::WriteAllBytes($specFile, $originalSpecBytes)
    [Environment]::SetEnvironmentVariable($smokeInputVariable, $originalSmokeInput, 'Process')
    $env:C_INCLUDE_PATH = $originalCIncludePath
    if (Test-Path -LiteralPath $smokeWorkspace) {
        Remove-Item -LiteralPath $smokeWorkspace -Recurse -Force
    }
    Pop-Location
}
