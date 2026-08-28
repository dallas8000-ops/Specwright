# Foreground UI only. Requires API on port 8088 in another tab.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location "$root\frontend"

$apiUp = $false
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8088/api/v1/health" -TimeoutSec 2 | Out-Null
    $apiUp = $true
} catch {
    $apiUp = $false
}

if (-not $apiUp) {
    Write-Host ""
    Write-Host "  API is NOT running on port 8088 - you will see ECONNREFUSED errors." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Open a SECOND terminal tab and run:" -ForegroundColor Yellow
    Write-Host ('    cd ' + $root) -ForegroundColor White
    Write-Host "    .\scripts\dev.ps1 -Api" -ForegroundColor White
    Write-Host ""
    Write-Host "  Then refresh the browser. Starting UI anyway..." -ForegroundColor DarkYellow
    Write-Host ""
} else {
    Write-Host "API OK on http://127.0.0.1:8088" -ForegroundColor Green
}

Write-Host "Specwright UI on http://localhost:5173 - press Ctrl+C to stop" -ForegroundColor Cyan
npm run dev
