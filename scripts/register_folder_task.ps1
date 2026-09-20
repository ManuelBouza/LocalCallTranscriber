[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][string]$InputDirectory,
    [Parameter(Mandatory)][string]$OutputDirectory,
    [string]$TaskName = 'LocalCallTranscriber-Folder',
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')][string]$Time = '02:00'
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $InputDirectory -PathType Container)) { throw "No existe: $InputDirectory" }
$runner = Join-Path $PSScriptRoot 'run_folder_task.ps1'
$action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runner`" -InputDirectory `"$InputDirectory`" -OutputDirectory `"$OutputDirectory`""
if ($PSCmdlet.ShouldProcess($TaskName, "Crear tarea diaria a las $Time")) {
    & schtasks.exe /Create /TN $TaskName /TR $action /SC DAILY /ST $Time /F
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear la tarea programada.' }
}
