$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "  Specwright smoke test" -ForegroundColor Cyan
Write-Host "  =====================" -ForegroundColor Cyan
Write-Host ""

Write-Host "  1/3 Frontend tests..." -ForegroundColor Yellow
Set-Location "$root\frontend"
npm run test:run

Write-Host ""
Write-Host "  2/3 API tests..." -ForegroundColor Yellow
Set-Location $root
& "$root\api\.venv\Scripts\python.exe" -m pytest api\tests -q

Write-Host ""
Write-Host "  3/3 Backend route smoke tests..." -ForegroundColor Yellow
Set-Location "$root\backend"
& "$root\backend\.venv\Scripts\python.exe" -m pytest apps\accounts\tests\test_route_coverage.py -q -o addopts=

Write-Host ""
Write-Host "  Smoke test completed successfully." -ForegroundColor Green
Write-Host ""
