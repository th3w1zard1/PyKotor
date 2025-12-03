#!/usr/bin/env pwsh
# Wrapper script for fix_help_tests_cleanup.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "fix_help_tests_cleanup.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "fix_help_tests_cleanup.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
