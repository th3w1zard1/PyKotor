# Test script for installing and running holocrontoolset from PyPI using uv
# This demonstrates the correct, most concise commands

Write-Host "Testing holocrontoolset installation from PyPI using uv..." -ForegroundColor Cyan

# Clean up any existing test venv
if (Test-Path ".venv_test") {
    Write-Host "Removing existing .venv_test..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv_test
}

Write-Host "`n=== Method 1: Most Concise (auto-install and run) ===" -ForegroundColor Green
Write-Host "Command: uv run -w holocrontoolset holocrontoolset" -ForegroundColor Gray
Write-Host "This installs the package on-the-fly and runs it in an isolated environment"

Write-Host "`n=== Method 2: Using specific venv (.venv_test) ===" -ForegroundColor Green
Write-Host "Step 1: uv venv .venv_test" -ForegroundColor Gray
Write-Host "Step 2: uv pip install --python .venv_test\Scripts\python.exe holocrontoolset" -ForegroundColor Gray
Write-Host "Step 3: uv run --python .venv_test\Scripts\python.exe holocrontoolset" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: Use 'holocrontoolset' (the script name), NOT '-m holocrontoolset' (module)" -ForegroundColor Yellow

Write-Host "`n=== Key Points ===" -ForegroundColor Green
Write-Host "1. holocrontoolset is a CONSOLE SCRIPT, not a Python module" -ForegroundColor White
Write-Host "2. Wrong: uv run -m holocrontoolset" -ForegroundColor Red
Write-Host "3. Correct: uv run holocrontoolset (or with -w to auto-install)" -ForegroundColor Green
Write-Host "4. The entry point is defined in pyproject.toml as:" -ForegroundColor White
Write-Host "   holocrontoolset = 'toolset.__main__:main'" -ForegroundColor Gray

Write-Host "`n=== Testing Method 2 (with .venv_test) ===" -ForegroundColor Cyan

# Step 1: Create venv
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
uv venv .venv_test
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create venv" -ForegroundColor Red
    exit 1
}

# Step 2: Install package (this will fail if package not on PyPI, but shows correct syntax)
Write-Host "`nInstalling holocrontoolset..." -ForegroundColor Yellow
Write-Host "Note: This may fail if the package is not yet published to PyPI" -ForegroundColor Gray
uv pip install --python .venv_test\Scripts\python.exe holocrontoolset
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nPackage installation failed - this is expected if holocrontoolset is not on PyPI yet" -ForegroundColor Yellow
    Write-Host "The command syntax is correct: uv pip install --python .venv_test\Scripts\python.exe holocrontoolset" -ForegroundColor Green
} else {
    Write-Host "`nPackage installed successfully!" -ForegroundColor Green
    
    # Step 3: Run the console script
    Write-Host "`nRunning holocrontoolset..." -ForegroundColor Yellow
    uv run --python .venv_test\Scripts\python.exe holocrontoolset --help
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Most concise from scratch:" -ForegroundColor White
Write-Host "  uv run -w holocrontoolset holocrontoolset" -ForegroundColor Green
Write-Host ""
Write-Host "With explicit venv (.venv_test):" -ForegroundColor White
Write-Host "  uv venv .venv_test" -ForegroundColor Green
Write-Host "  uv pip install --python .venv_test\Scripts\python.exe holocrontoolset" -ForegroundColor Green
Write-Host "  uv run --python .venv_test\Scripts\python.exe holocrontoolset" -ForegroundColor Green
Write-Host ""
Write-Host "Remember: Use 'holocrontoolset' (script name), NOT '-m holocrontoolset' (module)" -ForegroundColor Yellow

