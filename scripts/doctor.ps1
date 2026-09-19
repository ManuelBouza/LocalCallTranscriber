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

$pythonInterpreters = [System.Collections.Generic.List[object]]::new()
$pythonLauncherEntries = [System.Collections.Generic.List[string]]::new()

function Add-PythonInterpreter {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Source
    )

    $existing = @($pythonInterpreters | Where-Object { $_.path -ieq $Path })
    if ($existing.Count -gt 0) {
        return
    }

    $versionResult = Get-CommandOutput -Command $Path -Arguments @('--version')
    $pythonInterpreters.Add([pscustomobject]@{
        path    = $Path
        source  = $Source
        version = if ($versionResult.succeeded) { $versionResult.output -join ' ' } else { $null }
    })
}

$pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
if ($null -ne $pyLauncher) {
    $launcherResult = Get-CommandOutput -Command $pyLauncher.Source -Arguments @('-0p')
    if ($launcherResult.succeeded) {
        foreach ($line in $launcherResult.output) {
            $pythonLauncherEntries.Add($line)
            if ($line -match '(?<path>[A-Za-z]:\\.+?python(?:\.exe)?)\s*$') {
                Add-PythonInterpreter -Path $Matches.path -Source 'py launcher'
            }
        }
    }
}

$pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -eq $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
}
if ($null -ne $pythonCommand) {
    Add-PythonInterpreter -Path $pythonCommand.Source -Source 'PATH'
}

if ($pythonInterpreters.Count -gt 0) {
    Add-Diagnostic -Component 'Python' -Status 'PASS' -Summary "$($pythonInterpreters.Count) intérprete(s) relevante(s) detectado(s)." -Details @{
        interpreters     = @($pythonInterpreters)
        launcher_entries = @($pythonLauncherEntries)
    }
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

$cudaPaths = [System.Collections.Generic.List[string]]::new()
foreach ($target in @('Process', 'User', 'Machine')) {
    $candidate = [Environment]::GetEnvironmentVariable('CUDA_PATH', $target)
    if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate -PathType Container) -and $cudaPaths -notcontains $candidate) {
        $cudaPaths.Add($candidate)
    }
}

$cudaToolkitRoot = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA'
if (Test-Path -LiteralPath $cudaToolkitRoot -PathType Container) {
    foreach ($directory in @(Get-ChildItem -LiteralPath $cudaToolkitRoot -Directory -ErrorAction SilentlyContinue)) {
        if ($cudaPaths -notcontains $directory.FullName) {
            $cudaPaths.Add($directory.FullName)
        }
    }
}

$nvccCandidates = [System.Collections.Generic.List[string]]::new()
$nvccCommand = Get-Command nvcc.exe -ErrorAction SilentlyContinue
if ($null -eq $nvccCommand) {
    $nvccCommand = Get-Command nvcc -ErrorAction SilentlyContinue
}
if ($null -ne $nvccCommand) {
    $nvccCandidates.Add($nvccCommand.Source)
}
foreach ($path in $cudaPaths) {
    $candidate = Join-Path $path 'bin\nvcc.exe'
    if ((Test-Path -LiteralPath $candidate -PathType Leaf) -and $nvccCandidates -notcontains $candidate) {
        $nvccCandidates.Add($candidate)
    }
}
if ($nvccCandidates.Count -gt 0) {
    $nvccResult = Get-CommandOutput -Command $nvccCandidates[0] -Arguments @('--version')
    if ($nvccResult.succeeded) {
        Add-Diagnostic -Component 'CUDA Toolkit' -Status 'PASS' -Summary 'CUDA toolkit detectable mediante nvcc.' -Details @{ nvcc = $nvccCandidates[0]; version = @($nvccResult.output); toolkit_paths = @($cudaPaths) }
    }
    else {
        Add-Diagnostic -Component 'CUDA Toolkit' -Status 'WARN' -Summary 'Se detectó nvcc, pero no devolvió una versión válida.' -Details @{ nvcc = $nvccCandidates[0]; output = @($nvccResult.output); toolkit_paths = @($cudaPaths) }
    }
}
elseif ($cudaPaths.Count -gt 0) {
    Add-Diagnostic -Component 'CUDA Toolkit' -Status 'WARN' -Summary 'Se detectaron directorios de CUDA, pero no nvcc.' -Details @{ toolkit_paths = @($cudaPaths) }
}
else {
    Add-Diagnostic -Component 'CUDA Toolkit' -Status 'NOT_FOUND' -Summary 'No se detectó CUDA toolkit.'
}

$runtimeRoots = [System.Collections.Generic.List[object]]::new()
$seenRuntimeRoots = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
function Add-RuntimeRoot {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Source
    )

    $normalized = $Path.Trim().Trim('"')
    if (-not [string]::IsNullOrWhiteSpace($normalized) -and (Test-Path -LiteralPath $normalized -PathType Container) -and $seenRuntimeRoots.Add($normalized)) {
        $runtimeRoots.Add([pscustomobject]@{ path = $normalized; source = $Source })
    }
}

foreach ($directory in ($env:Path -split [System.IO.Path]::PathSeparator)) {
    Add-RuntimeRoot -Path $directory -Source 'process PATH'
}
foreach ($path in $cudaPaths) {
    Add-RuntimeRoot -Path (Join-Path $path 'bin') -Source 'CUDA installation'
}
Add-RuntimeRoot -Path 'C:\Program Files\NVIDIA Corporation\NVSMI' -Source 'NVIDIA NVSMI'

$libraryDefinitions = @(
    [pscustomobject]@{ category = 'CUDA Runtime'; pattern = 'cudart64*.dll' },
    [pscustomobject]@{ category = 'cuBLAS'; pattern = 'cublas64*.dll' },
    [pscustomobject]@{ category = 'cuBLAS'; pattern = 'cublasLt64*.dll' },
    [pscustomobject]@{ category = 'cuDNN'; pattern = 'cudnn*.dll' }
)
$runtimeLibraries = [System.Collections.Generic.List[object]]::new()
$seenLibraryPaths = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($root in $runtimeRoots) {
    foreach ($definition in $libraryDefinitions) {
        foreach ($library in @(Get-ChildItem -LiteralPath $root.path -Filter $definition.pattern -File -ErrorAction SilentlyContinue)) {
            if ($seenLibraryPaths.Add($library.FullName)) {
                $runtimeLibraries.Add([pscustomobject]@{
                    category = $definition.category
                    name     = $library.Name
                    path     = $library.FullName
                    source   = $root.source
                })
            }
        }
    }
}

foreach ($runtimeComponent in @('CUDA Runtime', 'cuBLAS', 'cuDNN')) {
    $libraries = @($runtimeLibraries | Where-Object { $_.category -eq $runtimeComponent })
    if ($libraries.Count -gt 0) {
        Add-Diagnostic -Component $runtimeComponent -Status 'PASS' -Summary "$($libraries.Count) biblioteca(s) $runtimeComponent detectada(s) para el proceso actual." -Details @{ libraries = @($libraries); search_roots = @($runtimeRoots) }
    }
    else {
        Add-Diagnostic -Component $runtimeComponent -Status 'NOT_FOUND' -Summary "No se detectaron bibliotecas $runtimeComponent en PATH ni ubicaciones NVIDIA conocidas." -Details @{ search_roots = @($runtimeRoots) }
    }
}
if (@($runtimeLibraries | Where-Object { $_.category -eq 'CUDA Runtime' }).Count -eq 0) {
    $recommendations.Add('No se detectó el runtime CUDA para el proceso actual; no se instalará durante el preflight. La compatibilidad se evaluará en la fase CUDA opcional.')
}

$ct2Checks = [System.Collections.Generic.List[object]]::new()
foreach ($interpreter in $pythonInterpreters) {
    $ct2Result = Get-CommandOutput -Command $interpreter.path -Arguments @('-c', 'import importlib.metadata, importlib.util; spec = importlib.util.find_spec("ctranslate2"); print(importlib.metadata.version("ctranslate2") if spec else "")')
    $version = if ($ct2Result.succeeded -and $ct2Result.output.Count -gt 0) { $ct2Result.output[0] } else { $null }
    $ct2Checks.Add([pscustomobject]@{
        interpreter = $interpreter.path
        source      = $interpreter.source
        installed   = ($null -ne $version)
        version     = $version
        error       = if ($ct2Result.succeeded) { $null } else { $ct2Result.output -join ' ' }
    })
}
$ct2Installed = @($ct2Checks | Where-Object { $_.installed })
if ($ct2Installed.Count -gt 0) {
    Add-Diagnostic -Component 'CTranslate2' -Status 'PASS' -Summary "CTranslate2 detectado en $($ct2Installed.Count) intérprete(s) Python." -Details @{ installed_in = @($ct2Installed); interpreter_checks = @($ct2Checks) }
}
elseif ($pythonInterpreters.Count -gt 0) {
    Add-Diagnostic -Component 'CTranslate2' -Status 'NOT_FOUND' -Summary 'CTranslate2 no está instalado en ninguno de los intérpretes Python detectados.' -Details @{ interpreter_checks = @($ct2Checks) }
}
else {
    Add-Diagnostic -Component 'CTranslate2' -Status 'NOT_FOUND' -Summary 'No se pudo comprobar CTranslate2 porque no se detectaron intérpretes Python.' -Details @{ interpreter_checks = @() }
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
