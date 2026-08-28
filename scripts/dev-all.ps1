# One terminal: API + UI together. Ctrl+C stops both.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$DevApiPort = 8088
$uvicorn = Join-Path $root "api\.venv\Scripts\uvicorn.exe"

if (-not (Test-Path $uvicorn)) {
    throw "API venv not found. Run: cd api; python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
}

& (Join-Path $root "scripts\stop-dev.ps1")
Start-Sleep -Seconds 1

$env:SPECWRIGHT_PUBLIC_API_URL = "http://127.0.0.1:$DevApiPort"
$env:SPECWRIGHT_PUBLIC_SITE_URL = "http://127.0.0.1:$DevApiPort"

Write-Host ""
Write-Host "  Specwright - API + UI (one terminal, Ctrl+C stops both)" -ForegroundColor Cyan
Write-Host "  API  http://127.0.0.1:$DevApiPort" -ForegroundColor Green
Write-Host "  UI   http://localhost:5173" -ForegroundColor Green
Write-Host ""

$logDir = Join-Path $root ".specwright"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$apiLog = Join-Path $logDir "api-dev.log"
$apiErrLog = Join-Path $logDir "api-dev.err.log"
# PowerShell requires separate files for stdout vs stderr redirects.
if (Test-Path $apiLog) { Remove-Item $apiLog -Force -ErrorAction SilentlyContinue }
if (Test-Path $apiErrLog) { Remove-Item $apiErrLog -Force -ErrorAction SilentlyContinue }

$apiProc = Start-Process `
    -FilePath $uvicorn `
    -ArgumentList @("api.main:app", "--reload", "--reload-dir", "api", "--port", "$DevApiPort") `
    -WorkingDirectory $root `
    -PassThru `
    -WindowStyle Hidden `
    -RedirectStandardOutput $apiLog `
    -RedirectStandardError $apiErrLog

function Stop-Api {
    if ($apiProc -and -not $apiProc.HasExited) {
        taskkill /F /T /PID $apiProc.Id 2>$null | Out-Null
    }
}

try {
    $ready = $false
    for ($i = 0; $i -lt 45; $i++) {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:$DevApiPort/api/v1/health" -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        Write-Host "API did not start on port $DevApiPort within 45s." -ForegroundColor Red
        if (Test-Path $apiLog) {
            Write-Host "Last lines from $apiLog :" -ForegroundColor Yellow
            Get-Content $apiLog -Tail 15 | ForEach-Object { Write-Host "  $_" }
        }
        if (Test-Path $apiErrLog) {
            Write-Host "Stderr from $apiErrLog :" -ForegroundColor Yellow
            Get-Content $apiErrLog -Tail 15 | ForEach-Object { Write-Host "  $_" }
        }
        throw "API failed to start. Run .\scripts\stop-dev.ps1 then .\scripts\dev.ps1"
    }
    Write-Host "API ready." -ForegroundColor Green
    Set-Location (Join-Path $root "frontend")
    npm run dev
} finally {
    Stop-Api
    Write-Host "Stopped API and UI." -ForegroundColor DarkYellow
}
