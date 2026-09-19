$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$doctorScript = Join-Path $repositoryRoot 'scripts/doctor.ps1'

if (-not (Test-Path -LiteralPath $doctorScript -PathType Leaf)) {
    throw "No se encontró el script de diagnóstico: $doctorScript"
}

$report = & $doctorScript -AsJson | ConvertFrom-Json
if ($null -eq $report.generated_at_utc) {
    throw 'El informe JSON no contiene generated_at_utc.'
}

$requiredComponents = @('Windows', 'PowerShell', 'Python', 'GPU NVIDIA', 'CUDA Toolkit', 'CUDA Runtime', 'cuBLAS', 'cuDNN', 'CTranslate2', 'Espacio libre')
$allowedStatuses = @('PASS', 'WARN', 'FAIL', 'NOT_FOUND')
foreach ($component in $requiredComponents) {
    $entry = @($report.diagnostics | Where-Object { $_.component -eq $component })
    if ($entry.Count -ne 1) {
        throw "Se esperaba exactamente un diagnóstico para '$component'; encontrados: $($entry.Count)."
    }
    if ($entry[0].status -notin $allowedStatuses) {
        throw "Estado no permitido para '$component': $($entry[0].status)."
    }
    if ([string]::IsNullOrWhiteSpace($entry[0].summary)) {
        throw "El diagnóstico '$component' no contiene resumen."
    }
}

$python = @($report.diagnostics | Where-Object { $_.component -eq 'Python' })[0]
if ($python.status -eq 'PASS' -and @($python.details.interpreters).Count -lt 1) {
    throw 'Python indica PASS, pero no informa intérpretes estructurados.'
}

$ct2 = @($report.diagnostics | Where-Object { $_.component -eq 'CTranslate2' })[0]
if ($null -eq $ct2.details.interpreter_checks) {
    throw 'CTranslate2 no informa las comprobaciones por intérprete.'
}
foreach ($check in @($ct2.details.interpreter_checks)) {
    if ([string]::IsNullOrWhiteSpace($check.interpreter)) {
        throw 'Una comprobación de CTranslate2 no identifica su intérprete.'
    }
    if ($null -eq $check.installed) {
        throw 'Una comprobación de CTranslate2 no indica si está instalado.'
    }
}

foreach ($component in @('CUDA Runtime', 'cuBLAS', 'cuDNN')) {
    $entry = @($report.diagnostics | Where-Object { $_.component -eq $component })[0]
    if ($null -eq $entry.details.search_roots) {
        throw "$component no informa las ubicaciones consultadas."
    }
    if ($entry.status -eq 'PASS' -and @($entry.details.libraries).Count -lt 1) {
        throw "$component indica PASS, pero no informa bibliotecas detectadas."
    }
}

if (@($report.recommendations).Count -lt 1) {
    throw 'El informe no contiene recomendaciones.'
}

Write-Host 'PASS: la estructura JSON del preflight es válida.' -ForegroundColor Green
