# Build a release wheel and/or Windows desktop bundle.
# Usage:
#   .\build.ps1           # wheel + exe
#   .\build.ps1 wheel     # installable wheel only
#   .\build.ps1 exe       # PyInstaller folder only

param(
    [ValidateSet("wheel", "exe", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Get-Python {
    $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        return $venvPy
    }
    return "python"
}

$Py = Get-Python
Write-Host "Using Python: $Py"

New-Item -ItemType Directory -Force -Path (Join-Path $Root "dist") | Out-Null

if ($Target -in @("wheel", "all")) {
    Write-Host "Building wheel..."
    & $Py -m pip install -q build
    & $Py -m build --wheel --outdir (Join-Path $Root "dist")
}

if ($Target -in @("exe", "all")) {
    Write-Host "Building desktop bundle..."
    & $Py -m pip install -q pyinstaller
    $work = Join-Path $Root "build\pyinstaller"
    New-Item -ItemType Directory -Force -Path $work | Out-Null
    & $Py -m PyInstaller `
        (Join-Path $Root "packaging\code_scenarios.spec") `
        --noconfirm `
        --distpath (Join-Path $Root "dist") `
        --workpath $work
}

Write-Host ""
Write-Host "Done."
Write-Host "  Wheel:  dist\code_scenarios-*.whl"
Write-Host "  Exe:    dist\CodeScenarios\CodeScenarios.exe"
