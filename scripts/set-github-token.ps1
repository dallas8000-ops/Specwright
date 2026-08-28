param(
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$Token,
    [switch]$AlsoDeploymentStripe
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $root ".env"

if (-not (Test-Path $envFile)) {
    throw ".env not found. Copy .env.specwright.example to .env first."
}

if (-not $Token) {
    Write-Host ""
    Write-Host "Run: .\scripts\set-github-token.ps1 YOUR_TOKEN_HERE" -ForegroundColor Cyan
    Write-Host "Or paste when prompted below." -ForegroundColor Cyan
    $Token = Read-Host "GitHub token"
}

$Token = $Token.Trim()
if (-not $Token) {
    throw "No token entered."
}

$lines = Get-Content $envFile -Encoding UTF8
$found = $false
$out = @()
foreach ($line in $lines) {
    if ($line -match '^\s*SPECWRIGHT_GITHUB_TOKEN=') {
        $found = $true
        $out += "SPECWRIGHT_GITHUB_TOKEN=$Token"
    } else {
        $out += $line
    }
}
if (-not $found) {
    $out += "SPECWRIGHT_GITHUB_TOKEN=$Token"
}
$out | Set-Content $envFile -Encoding UTF8

Write-Host "Updated SPECWRIGHT_GITHUB_TOKEN in .env" -ForegroundColor Green
Write-Host "Restart: .\scripts\dev.ps1" -ForegroundColor Yellow

$saveDsc = $AlsoDeploymentStripe
if (-not $AlsoDeploymentStripe) {
    $answer = Read-Host 'Also save to Deployment-Stripe-center private_env\github.env? y/N'
    $saveDsc = $answer -match '^[yY]'
}

if ($saveDsc) {
    $dscRoot = 'C:\Software Projects\Deployment-Stripe-center\private_env'
    $githubEnv = Join-Path $dscRoot 'github.env'
    if (-not (Test-Path $dscRoot)) {
        Write-Warning 'Deployment-Stripe-center private_env not found - skipped.'
    } else {
        if (-not (Test-Path $githubEnv)) {
            Copy-Item (Join-Path $dscRoot 'github.env.example') $githubEnv
        }
        $gLines = Get-Content $githubEnv -Encoding UTF8
        $gFound = $false
        $gOut = @()
        foreach ($line in $gLines) {
            if ($line -match '^\s*GITHUB_TOKEN=') {
                $gFound = $true
                $gOut += "GITHUB_TOKEN=$Token"
            } else {
                $gOut += $line
            }
        }
        if (-not $gFound) {
            $gOut += "GITHUB_TOKEN=$Token"
        }
        $gOut | Set-Content $githubEnv -Encoding UTF8
        Write-Host 'Updated GITHUB_TOKEN in Deployment-Stripe-center\private_env\github.env' -ForegroundColor Green
    }
}
