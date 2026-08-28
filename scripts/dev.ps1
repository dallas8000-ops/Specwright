# Start Specwright — one command, one terminal (API + UI).
param(
    [switch]$Api,
    [switch]$Ui
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if ($Api) {
    & (Join-Path $root "scripts\dev-api.ps1")
    exit $LASTEXITCODE
}
if ($Ui) {
    & (Join-Path $root "scripts\dev-ui.ps1")
    exit $LASTEXITCODE
}

& (Join-Path $root "scripts\dev-all.ps1")
