# Generate and open the Allure HTML report from pytest raw results.
param(
    [string]$ResultsDir = "allure-results",
    [string]$ReportDir = "allure-report",
    [switch]$ServeOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path $ResultsDir)) {
    Write-Error "No Allure results at '$ResultsDir'. Run pytest first."
}

$allure = Get-Command allure -ErrorAction SilentlyContinue
if (-not $allure) {
    Write-Host @"
Allure CLI is not on PATH.

Install one of:
  scoop install allure
  choco install allure-commandline

Or run:  allure serve $ResultsDir
"@
    exit 1
}

if ($ServeOnly) {
    Write-Host "Serving Allure report from $ResultsDir ..."
    allure serve $ResultsDir
    exit $LASTEXITCODE
}

Write-Host "Generating Allure report: $ReportDir"
allure generate $ResultsDir -o $ReportDir --clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$index = Join-Path $ReportDir "index.html"
Write-Host "Report ready: $index"
Start-Process $index
