[CmdletBinding(SupportsShouldProcess)]
param([string]$TaskName = 'LocalCallTranscriber-Folder')

$ErrorActionPreference = 'Stop'
if ($PSCmdlet.ShouldProcess($TaskName, 'Eliminar tarea programada')) {
    & schtasks.exe /Delete /TN $TaskName /F
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo eliminar la tarea programada.' }
}
