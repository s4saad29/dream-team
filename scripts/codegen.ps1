# Launch Playwright Inspector and generate pytest code from your actions.
# Usage:
#   .\scripts\codegen.ps1                    # login page
#   .\scripts\codegen.ps1 -Dashboard         # dashboard (uses saved auth if present)
#   .\scripts\codegen.ps1 -Profile           # profile page
#   .\scripts\codegen.ps1 -Output tests\generated\recorded_test.py

param(
    [switch]$Dashboard,
    [switch]$Profile,
    [string]$Output = "",
    [string]$Url = ""
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$BaseUrl = if ($env:BASE_URL) { $env:BASE_URL } else { "https://team.addo.ai" }
$TargetUrl = switch ($true) {
    { $Url } { $Url }
    $Profile { "$BaseUrl/dashboard" }
    $Dashboard { "$BaseUrl/dashboard" }
    default { "$BaseUrl/login" }
}

$Args = @(
    "codegen",
    "--target=python-pytest",
    "--viewport-size=1280,720",
    "--ignore-https-errors",
    $TargetUrl
)

$StoragePath = Join-Path $ProjectRoot "auth\storage_state.json"
if (($Dashboard -or $Profile) -and (Test-Path $StoragePath)) {
    $Args += "--load-storage=$StoragePath"
    Write-Host "Using auth: $StoragePath"
}

if ($Output) {
    $OutDir = Split-Path -Parent $Output
    if ($OutDir -and -not (Test-Path $OutDir)) {
        New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    }
    $Args += "-o", $Output
    Write-Host "Output file: $Output"
}

Write-Host "Playwright pytest codegen -> $TargetUrl"
Write-Host "Command: playwright $($Args -join ' ')"
playwright @Args
