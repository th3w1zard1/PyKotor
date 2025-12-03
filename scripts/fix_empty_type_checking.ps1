#!/usr/bin/env pwsh
# Wrapper script for fix_empty_type_checking.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "fix_empty_type_checking.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "fix_empty_type_checking.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
