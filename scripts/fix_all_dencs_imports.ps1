#!/usr/bin/env pwsh
# Wrapper script for fix_all_dencs_imports.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "fix_all_dencs_imports.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "fix_all_dencs_imports.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
