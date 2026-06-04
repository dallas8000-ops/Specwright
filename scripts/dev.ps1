# Start Specwright API + UI with visible console output
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host ""
Write-Host "  Specwright dev stack" -ForegroundColor Cyan
Write-Host "  ====================" -ForegroundColor Cyan
Write-Host ""

$apiCmd = "Set-Location '$root'; & '$root\api\.venv\Scripts\uvicorn.exe' api.main:app --reload --port 8080"
$uiCmd = "Set-Location '$root\frontend'; npm run dev"

Write-Host "  API  -> http://127.0.0.1:8080  (landing page with links)" -ForegroundColor Green
Write-Host "  UI   -> http://localhost:5173  (Vite may use 5174 if busy)" -ForegroundColor Green
Write-Host ""
foreach ($port in 5173, 5174, 5175) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    Write-Host "  Stopping stale process on port $port (PID $($c.OwningProcess))..." -ForegroundColor DarkYellow
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
  }
}

Write-Host "  Starting API in a new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd

Start-Sleep -Seconds 2
Write-Host "  Starting UI in a new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", $uiCmd

Write-Host ""
Write-Host "  Open the UI link above in your browser (not port 8080 alone for the app)." -ForegroundColor White
Write-Host ""
