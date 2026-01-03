<#
.SYNOPSIS
    Installs and runs holocrontoolset from PyPI using uv exclusively.

.DESCRIPTION
    This script demonstrates the correct, most concise commands to install and run
    holocrontoolset from PyPI using uv. The key issue with the original command was
    using '-m holocrontoolset' (trying to run as a module) when it should be run
    as a console script (just 'holocrontoolset').

.EXAMPLE
    .\install_holocrontoolset_from_pypi.ps1
    Installs and runs holocrontoolset using the .venv_test virtual environment.

.NOTES
    - holocrontoolset is a CONSOLE SCRIPT, not a Python module
    - Wrong: uv run -m holocrontoolset
    - Correct: uv run holocrontoolset
#>

param(
    [switch]$RunAfterInstall,
    [string]$VenvName = ".venv_test"
)

Write-Host "=== Installing holocrontoolset from PyPI using uv ===" -ForegroundColor Cyan

# Clean up any existing test venv
if (Test-Path $VenvName) {
    Write-Host "`nRemoving existing $VenvName..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $VenvName
}

# Step 1: Create venv
Write-Host "`n[1/3] Creating virtual environment: $VenvName" -ForegroundColor Yellow
uv venv $VenvName
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Step 2: Install package
Write-Host "`n[2/3] Installing holocrontoolset from PyPI..." -ForegroundColor Yellow
$pythonExe = Join-Path $VenvName "Scripts\python.exe"
uv pip install --python $pythonExe holocrontoolset
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nFailed to install holocrontoolset. The package may not be published to PyPI yet." -ForegroundColor Red
    Write-Host "However, the command syntax is correct:" -ForegroundColor Yellow
    Write-Host "  uv pip install --python $pythonExe holocrontoolset" -ForegroundColor Gray
    exit 1
}

Write-Host "`nPackage installed successfully!" -ForegroundColor Green

if ($RunAfterInstall) {
    # Step 3: Run the console script
    Write-Host "`n[3/3] Running holocrontoolset..." -ForegroundColor Yellow
    uv run --python $pythonExe holocrontoolset --help
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Most concise commands from scratch:" -ForegroundColor White
Write-Host ""
Write-Host "With explicit venv ($VenvName):" -ForegroundColor Green
Write-Host "  uv venv $VenvName" -ForegroundColor Gray
Write-Host "  uv pip install --python $VenvName\Scripts\python.exe holocrontoolset" -ForegroundColor Gray
Write-Host "  uv run --python $VenvName\Scripts\python.exe holocrontoolset" -ForegroundColor Gray
Write-Host ""
Write-Host "Auto-managed (uv handles venv):" -ForegroundColor Green
Write-Host "  uv run -w holocrontoolset holocrontoolset" -ForegroundColor Gray
Write-Host ""
Write-Host "Key point: Use 'holocrontoolset' (script name), NOT '-m holocrontoolset' (module)" -ForegroundColor Yellow

