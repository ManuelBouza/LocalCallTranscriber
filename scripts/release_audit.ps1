[CmdletBinding()]
param(
    [switch]$SkipPackage
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$expectedVersion = '0.2.0'

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    throw 'No se encontró .venv. Ejecuta .\scripts\bootstrap.ps1 -WithGui.'
}

Push-Location $repositoryRoot
try {
    $status = (& git status --porcelain)
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo consultar git status.'
    }
    if ($status) {
        throw 'El árbol de trabajo debe estar limpio antes de la auditoría de release.'
    }

    $existingTag = (& git tag --list "v$expectedVersion")
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo consultar los tags.'
    }
    if ($existingTag) {
        throw "El tag v$expectedVersion ya existe; la auditoría previa al release exige que todavía no se haya creado."
    }

    $projectVersion = & $venvPython -c 'import tomllib, pathlib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])'
    if ($LASTEXITCODE -ne 0 -or $projectVersion.ToString().Trim() -ne $expectedVersion) {
        throw "pyproject.toml debe declarar version=$expectedVersion."
    }

    & (Join-Path $repositoryRoot 'scripts\test.ps1')
    if ($LASTEXITCODE -ne 0) {
        throw 'La suite de pruebas falló.'
    }

    & $venvPython -m pip check
    if ($LASTEXITCODE -ne 0) {
        throw 'pip check detectó dependencias incompatibles.'
    }

    $tracked = @(& git ls-files)
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo enumerar el contenido versionado.'
    }
    $forbiddenExtensions = @(
        '.mp4', '.m4a', '.mp3', '.wav', '.flac', '.avi', '.mov', '.mkv',
        '.srt', '.vtt', '.gguf', '.safetensors', '.onnx'
    )
    $forbiddenTracked = @(
        $tracked | Where-Object {
            $extension = [IO.Path]::GetExtension($_).ToLowerInvariant()
            $forbiddenExtensions -contains $extension
        }
    )
    if ($forbiddenTracked.Count -gt 0) {
        throw "Hay multimedia, transcripciones o modelos versionados: $($forbiddenTracked -join ', ')"
    }

    $secretPattern = '(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16})'
    $secretMatches = @(& git grep -I -n -E $secretPattern -- . 2>$null)
    if ($LASTEXITCODE -eq 0 -and $secretMatches.Count -gt 0) {
        throw "Se detectaron patrones con aspecto de secreto: $($secretMatches -join [Environment]::NewLine)"
    }
    if ($LASTEXITCODE -notin @(0, 1)) {
        throw 'La búsqueda de secretos falló.'
    }

    if (-not $SkipPackage) {
        & (Join-Path $repositoryRoot 'scripts\package_gui.ps1')
        if ($LASTEXITCODE -ne 0) {
            throw 'La validación del paquete GUI falló.'
        }
    }

    Write-Host 'PASS: auditoría de release v0.2.0 completada.' -ForegroundColor Green
}
finally {
    Pop-Location
}
