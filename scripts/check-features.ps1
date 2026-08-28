# Quick check that the dev API sees your .env keys (uses port 8088).
$ErrorActionPreference = "Stop"
$url = "http://127.0.0.1:8088/api/v1/features"
try {
    $f = Invoke-RestMethod -Uri $url -TimeoutSec 8
    $f | Format-List
    if ($f.ai_suite -and $f.github) {
        Write-Host "OK - AI and GitHub keys loaded." -ForegroundColor Green
        exit 0
    }
    Write-Host "Keys missing - check .env and restart: .\scripts\dev.ps1 -Api" -ForegroundColor Red
    Write-Host "Do NOT test port 8080; dev API runs on 8088." -ForegroundColor Yellow
    exit 1
} catch {
    Write-Host "Could not reach $url" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host "Start API first: .\scripts\dev.ps1 -Api" -ForegroundColor Yellow
    exit 1
}
