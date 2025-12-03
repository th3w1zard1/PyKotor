#!/usr/bin/env pwsh
# Wrapper script for check_kit_completeness.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "check_kit_completeness.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "check_kit_completeness.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
