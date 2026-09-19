[CmdletBinding()]
param(
    [switch]$AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$results = [System.Collections.Generic.List[object]]::new()
$recommendations = [System.Collections.Generic.List[string]]::new()

function Add-Diagnostic {
    param(
        [Parameter(Mandatory)][string]$Component,
        [Parameter(Mandatory)][ValidateSet('PASS', 'WARN', 'FAIL', 'NOT_FOUND')][string]$Status,
        [Parameter(Mandatory)][string]$Summary,
        [hashtable]$Details = @{}
    )

    $results.Add([pscustomobject]@{
        component = $Component
        status    = $Status
        summary   = $Summary
        details   = [pscustomobject]$Details
    })
}

function Get-CommandOutput {
    param(
        [Parameter(Mandatory)][string]$Command,
        [string[]]$Arguments = @()
    )

    try {
        $output = & $Command @Arguments 2>&1
        return [pscustomobject]@{
            succeeded = ($LASTEXITCODE -eq 0)
            output    = @($output | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ })
        }
    }
    catch {
        return [pscustomobject]@{
            succeeded = $false
            output    = @($_.Exception.Message)
        }
    }
}

try {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    Add-Diagnostic -Component 'Windows' -Status 'PASS' -Summary "$($os.Caption) $($os.Version) (build $($os.BuildNumber))" -Details @{
        caption = $os.Caption
        version = $os.Version
        build   = $os.BuildNumber
    }
}
catch {
    try {
        $windowsVersion = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
        $release = if ($windowsVersion.DisplayVersion) { $windowsVersion.DisplayVersion } else { $windowsVersion.ReleaseId }
        Add-Diagnostic -Component 'Windows' -Status 'PASS' -Summary "$($windowsVersion.ProductName) $release (build $($windowsVersion.CurrentBuild))" -Details @{
            caption = $windowsVersion.ProductName
            version = $release
            build   = $windowsVersion.CurrentBuild
            source  = 'Registry fallback'
        }
    }
    catch {
        Add-Diagnostic -Component 'Windows' -Status 'FAIL' -Summary 'No se pudo consultar la versión de Windows.' -Details @{ error = $_.Exception.Message }
    }
}

Add-Diagnostic -Component 'PowerShell' -Status 'PASS' -Summary "PowerShell $($PSVersionTable.PSVersion)" -Details @{
    version = $PSVersionTable.PSVersion.ToString()
    edition = $PSVersionTable.PSEdition
}

$pythonInstallations = [System.Collections.Generic.List[string]]::new()
$pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
if ($null -ne $pyLauncher) {
    $launcherResult = Get-CommandOutput -Command $pyLauncher.Source -Arguments @('-0p')
    if ($launcherResult.succeeded) {
        foreach ($line in $launcherResult.output) {
            $pythonInstallations.Add($line)
        }
    }
}

$pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -eq $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
}
if ($null -ne $pythonCommand) {
    $versionResult = Get-CommandOutput -Command $pythonCommand.Source -Arguments @('--version')
    if ($versionResult.succeeded) {
        $pythonInstallations.Add("PATH: $($pythonCommand.Source) ($($versionResult.output -join ' '))")
    }
    else {
        $pythonInstallations.Add("PATH: $($pythonCommand.Source)")
    }
}

if ($pythonInstallations.Count -gt 0) {
    Add-Diagnostic -Component 'Python' -Status 'PASS' -Summary "$($pythonInstallations.Count) instalación(es) relevante(s) detectada(s)." -Details @{ installations = @($pythonInstallations) }
}
else {
    Add-Diagnostic -Component 'Python' -Status 'NOT_FOUND' -Summary 'No se detectó Python mediante el launcher ni PATH.'
    $recommendations.Add('Instala Python 3.11 o superior antes de la fase Bootstrap; no se ha instalado nada durante este preflight.')
}

$nvidiaAdapters = @()
$videoControllerError = $null
try {
    $nvidiaAdapters = @(Get-CimInstance -ClassName Win32_VideoController | Where-Object { $_.Name -match 'NVIDIA' })
}
catch {
    $videoControllerError = $_.Exception.Message
}

$nvidiaSmi = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
if ($null -eq $nvidiaSmi) {
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
}

if ($null -ne $nvidiaSmi) {
    $smiResult = Get-CommandOutput -Command $nvidiaSmi.Source -Arguments @('--query-gpu=name,driver_version,memory.total', '--format=csv,noheader')
    if ($smiResult.succeeded) {
        Add-Diagnostic -Component 'GPU NVIDIA' -Status 'PASS' -Summary "$($smiResult.output.Count) GPU(s) NVIDIA detectada(s) mediante nvidia-smi." -Details @{
            nvidia_smi = $nvidiaSmi.Source
            gpus       = @($smiResult.output)
            cim_warning = $videoControllerError
        }
    }
    else {
        Add-Diagnostic -Component 'GPU NVIDIA' -Status 'WARN' -Summary 'nvidia-smi existe, pero no pudo consultar la GPU.' -Details @{ nvidia_smi = $nvidiaSmi.Source; output = @($smiResult.output) }
    }
}
elseif ($nvidiaAdapters.Count -gt 0) {
    $adapterDetails = foreach ($adapter in $nvidiaAdapters) {
        [pscustomobject]@{
            name        = $adapter.Name
            driver      = $adapter.DriverVersion
            vram_bytes  = $adapter.AdapterRAM
        }
    }
    Add-Diagnostic -Component 'GPU NVIDIA' -Status 'WARN' -Summary 'Se detectó una GPU NVIDIA, pero nvidia-smi no está disponible en PATH.' -Details @{ gpus = @($adapterDetails); cim_warning = $videoControllerError }
    $recommendations.Add('Una GPU NVIDIA fue detectada sin nvidia-smi disponible; valida el driver antes de evaluar CUDA en la fase correspondiente.')
}
elseif ($null -ne $videoControllerError) {
    Add-Diagnostic -Component 'GPU NVIDIA' -Status 'WARN' -Summary 'No se pudo comprobar la GPU NVIDIA mediante CIM y nvidia-smi no está disponible.' -Details @{ cim_error = $videoControllerError }
}
else {
    Add-Diagnostic -Component 'GPU NVIDIA' -Status 'NOT_FOUND' -Summary 'No se detectó GPU NVIDIA.'
    $recommendations.Add('No se detectó GPU NVIDIA; la ruta CPU seguirá siendo la ruta operativa obligatoria.')
}

$cudaPath = [Environment]::GetEnvironmentVariable('CUDA_PATH', 'Process')
if ([string]::IsNullOrWhiteSpace($cudaPath)) {
    $cudaPath = [Environment]::GetEnvironmentVariable('CUDA_PATH', 'User')
}
if ([string]::IsNullOrWhiteSpace($cudaPath)) {
    $cudaPath = [Environment]::GetEnvironmentVariable('CUDA_PATH', 'Machine')
}

$nvcc = Get-Command nvcc.exe -ErrorAction SilentlyContinue
if ($null -eq $nvcc) {
    $nvcc = Get-Command nvcc -ErrorAction SilentlyContinue
}
if ($null -ne $nvcc) {
    $nvccResult = Get-CommandOutput -Command $nvcc.Source -Arguments @('--version')
    if ($nvccResult.succeeded) {
        Add-Diagnostic -Component 'CUDA' -Status 'PASS' -Summary 'CUDA toolkit detectable mediante nvcc.' -Details @{ nvcc = $nvcc.Source; version = @($nvccResult.output); cuda_path = $cudaPath }
    }
    else {
        Add-Diagnostic -Component 'CUDA' -Status 'WARN' -Summary 'nvcc existe, pero no devolvió una versión válida.' -Details @{ nvcc = $nvcc.Source; output = @($nvccResult.output) }
    }
}
elseif (-not [string]::IsNullOrWhiteSpace($cudaPath) -and (Test-Path -LiteralPath $cudaPath -PathType Container)) {
    Add-Diagnostic -Component 'CUDA' -Status 'WARN' -Summary 'CUDA_PATH apunta a un directorio existente, pero nvcc no está disponible en PATH.' -Details @{ cuda_path = $cudaPath }
}
else {
    Add-Diagnostic -Component 'CUDA' -Status 'NOT_FOUND' -Summary 'No se detectó CUDA toolkit.'
    $recommendations.Add('CUDA no está disponible actualmente; no se instalará durante el preflight. La compatibilidad se evaluará en la fase CUDA opcional.')
}

$cudnnFiles = @()
if (-not [string]::IsNullOrWhiteSpace($cudaPath) -and (Test-Path -LiteralPath $cudaPath -PathType Container)) {
    try {
        $cudnnFiles = @(Get-ChildItem -Path (Join-Path $cudaPath 'bin') -Filter 'cudnn*.dll' -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
    }
    catch {
        $cudnnFiles = @()
    }
}
if ($cudnnFiles.Count -gt 0) {
    Add-Diagnostic -Component 'cuDNN' -Status 'PASS' -Summary "$($cudnnFiles.Count) biblioteca(s) cuDNN detectada(s) junto a CUDA_PATH." -Details @{ files = @($cudnnFiles); cuda_path = $cudaPath }
}
else {
    Add-Diagnostic -Component 'cuDNN' -Status 'NOT_FOUND' -Summary 'No se detectó cuDNN en la ubicación CUDA_PATH consultada.'
}

if ($null -ne $pythonCommand) {
    $ct2Result = Get-CommandOutput -Command $pythonCommand.Source -Arguments @('-c', 'import importlib.util; print(importlib.util.find_spec("ctranslate2") is not None)')
    if ($ct2Result.succeeded -and (($ct2Result.output -join '').ToLowerInvariant() -eq 'true')) {
        Add-Diagnostic -Component 'CTranslate2' -Status 'PASS' -Summary 'CTranslate2 está instalado para el Python disponible en PATH.' -Details @{ python = $pythonCommand.Source }
    }
    else {
        Add-Diagnostic -Component 'CTranslate2' -Status 'NOT_FOUND' -Summary 'CTranslate2 no está instalado para el Python disponible en PATH.' -Details @{ python = $pythonCommand.Source }
    }
}
else {
    Add-Diagnostic -Component 'CTranslate2' -Status 'NOT_FOUND' -Summary 'No se pudo comprobar CTranslate2 porque Python no está disponible en PATH.'
}

try {
    $rootPath = [System.IO.Path]::GetPathRoot((Resolve-Path -LiteralPath $PSScriptRoot).Path)
    $drive = [System.IO.DriveInfo]::new($rootPath)
    $freeGiB = [Math]::Round($drive.AvailableFreeSpace / 1GB, 2)
    $totalGiB = [Math]::Round($drive.TotalSize / 1GB, 2)
    Add-Diagnostic -Component 'Espacio libre' -Status 'PASS' -Summary "$freeGiB GiB libres de $totalGiB GiB en $rootPath" -Details @{ root = $rootPath; free_gib = $freeGiB; total_gib = $totalGiB }
}
catch {
    Add-Diagnostic -Component 'Espacio libre' -Status 'FAIL' -Summary 'No se pudo consultar el espacio libre de la unidad del repositorio.' -Details @{ error = $_.Exception.Message }
}

if ($recommendations.Count -eq 0) {
    $recommendations.Add('El preflight no requiere cambios. Valida la combinación real de GPU solo en la fase CUDA opcional.')
}

$report = [pscustomobject]@{
    generated_at_utc = [DateTime]::UtcNow.ToString('o')
    diagnostics      = @($results)
    recommendations  = @($recommendations)
}

if ($AsJson) {
    $report | ConvertTo-Json -Depth 6
    return
}

Write-Host 'LocalCallTranscriber — Preflight' -ForegroundColor Cyan
foreach ($result in $results) {
    $colour = switch ($result.status) {
        'PASS' { 'Green' }
        'WARN' { 'Yellow' }
        'FAIL' { 'Red' }
        default { 'DarkYellow' }
    }
    Write-Host "[$($result.status)] $($result.component): $($result.summary)" -ForegroundColor $colour
}
Write-Host ''
Write-Host 'Recomendaciones:' -ForegroundColor Cyan
foreach ($recommendation in $recommendations) {
    Write-Host "- $recommendation"
}
