# Foreground API only — Ctrl+C to stop. Port 8088 (not 8080).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$DevApiPort = 8088
$env:SPECWRIGHT_PUBLIC_API_URL = "http://127.0.0.1:$DevApiPort"
$env:SPECWRIGHT_PUBLIC_SITE_URL = "http://127.0.0.1:$DevApiPort"

Write-Host "Specwright API on http://127.0.0.1:$DevApiPort (Ctrl+C to stop)" -ForegroundColor Cyan
# Only reload when api/ changes — not .specwright/repos/ (watch mode writes there and kills the server).
& "$root\api\.venv\Scripts\uvicorn.exe" api.main:app --reload --reload-dir api --port $DevApiPort
