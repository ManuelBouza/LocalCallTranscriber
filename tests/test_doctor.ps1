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

$requiredComponents = @('Windows', 'PowerShell', 'Python', 'GPU NVIDIA', 'CUDA', 'cuDNN', 'CTranslate2', 'Espacio libre')
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

if (@($report.recommendations).Count -lt 1) {
    throw 'El informe no contiene recomendaciones.'
}

Write-Host 'PASS: la estructura JSON del preflight es válida.' -ForegroundColor Green
