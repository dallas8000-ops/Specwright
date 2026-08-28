# Stop ALL Specwright dev processes (API, UI, stray PowerShell windows).
$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$rootEsc = [regex]::Escape($root)

Write-Host "Stopping Specwright dev processes..." -ForegroundColor Yellow

function Stop-PortListeners {
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        for ($pass = 0; $pass -lt 5; $pass++) {
            $pids = @(
                Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
                    Select-Object -ExpandProperty OwningProcess -Unique
            )
            if (-not $pids -or $pids.Count -eq 0) { break }
            foreach ($procId in $pids) {
                if ($procId -and $procId -gt 0) {
                    Write-Host "  Port $port -> PID $procId"
                    taskkill /F /T /PID $procId 2>$null | Out-Null
                }
            }
            Start-Sleep -Milliseconds 400
        }
    }
}

Stop-PortListeners -Ports @(8088, 8080, 5173, 5174, 5175)

# Specwright uvicorn / node / npm left from dev windows or agent runs
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $cmd = $_.CommandLine
        if (-not $cmd) { return $false }
        ($cmd -like "*Specwright*" -and (
            $cmd -like "*uvicorn*" -or
            $cmd -like "*api.main:app*" -or
            $cmd -like "*frontend*npm run dev*" -or
            $cmd -like "*vite*"
        ))
    } |
    ForEach-Object {
        Write-Host "  $($_.Name) PID $($_.ProcessId)"
        taskkill /F /T /PID $_.ProcessId 2>$null | Out-Null
    }

# PowerShell windows opened by old dev.ps1 (NoExit + uvicorn or npm)
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $cmd = $_.CommandLine
        $cmd -and $cmd -like "*Specwright*" -and (
            $cmd -like "*uvicorn*" -or $cmd -like "*npm run dev*"
        )
    } |
    ForEach-Object {
        if ($_.ProcessId -ne $PID) {
            Write-Host "  dev shell PID $($_.ProcessId)"
            taskkill /F /T /PID $_.ProcessId 2>$null | Out-Null
        }
    }

Get-Job -ErrorAction SilentlyContinue | Stop-Job -ErrorAction SilentlyContinue
Get-Job -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1
$left8088 = @(Get-NetTCPConnection -LocalPort 8088 -State Listen -ErrorAction SilentlyContinue).Count
$left5173 = @(Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue).Count
Write-Host ""
if ($left8088 -eq 0 -and $left5173 -eq 0) {
    Write-Host "Stopped. Ports 8088 and 5173 are free." -ForegroundColor Green
} else {
    Write-Host "Some listeners remain (8088=$left8088, 5173=$left5173)." -ForegroundColor Red
    Write-Host "Close any leftover 'Specwright API' / 'Specwright UI' PowerShell windows manually." -ForegroundColor Yellow
}
