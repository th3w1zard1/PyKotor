#!/usr/bin/env pwsh
# Wrapper script for fix_qss_variables.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "fix_qss_variables.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "fix_qss_variables.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
