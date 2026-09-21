[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$StatusPath,
    [Parameter(Mandatory = $true)]
    [string]$LogPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$packageScript = Join-Path $repositoryRoot 'scripts\package_gui.ps1'
$manifestPath = Join-Path $repositoryRoot 'dist\package-manifest.json'
$startedAt = (Get-Date).ToUniversalTime().ToString('o')

function Write-BuildStatus {
    param(
        [Parameter(Mandatory = $true)]
        [string]$State,
        [AllowNull()]
        [Nullable[int]]$ExitCode,
        [AllowNull()]
        [string]$ErrorMessage
    )

    $payload = [ordered]@{
        state = $State
        pid = $PID
        command = '.\scripts\package_gui.ps1'
        powershell_edition = $PSVersionTable.PSEdition
        powershell_version = $PSVersionTable.PSVersion.ToString()
        started_at = $startedAt
        finished_at = if ($State -eq 'RUNNING') { $null } else { (Get-Date).ToUniversalTime().ToString('o') }
        exit_code = $ExitCode
        log = $LogPath
        manifest = $manifestPath
        error = $ErrorMessage
    }

    $statusDirectory = Split-Path -Parent $StatusPath
    New-Item -ItemType Directory -Path $statusDirectory -Force | Out-Null
    $temporaryPath = "$StatusPath.tmp"
    $payload | ConvertTo-Json | Set-Content -LiteralPath $temporaryPath -Encoding utf8
    Move-Item -LiteralPath $temporaryPath -Destination $StatusPath -Force
}

New-Item -ItemType Directory -Path (Split-Path -Parent $LogPath) -Force | Out-Null
"[$startedAt] package build started (PID=$PID)" | Set-Content -LiteralPath $LogPath -Encoding utf8
Write-BuildStatus -State 'RUNNING' -ExitCode $null -ErrorMessage $null

try {
    & $packageScript *>> $LogPath
    Write-BuildStatus -State 'SUCCESS' -ExitCode 0 -ErrorMessage $null
    exit 0
}
catch {
    $message = $_.Exception.Message
    $_ | Out-String | Add-Content -LiteralPath $LogPath
    Write-BuildStatus -State 'FAILED' -ExitCode 1 -ErrorMessage $message
    exit 1
}
