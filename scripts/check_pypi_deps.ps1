#!/usr/bin/env pwsh
# Wrapper script for check_pypi_deps.py
# Calls the Python script to check PyPI package dependencies and metadata

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "check_pypi_deps.py"

if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "check_pypi_deps.py not found at $pythonScript"
    exit 1
}

# Pass all arguments to the Python script
python $pythonScript $args
exit $LASTEXITCODE
