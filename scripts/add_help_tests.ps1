#!/usr/bin/env pwsh
# Wrapper script for add_help_tests.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "add_help_tests.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "add_help_tests.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
