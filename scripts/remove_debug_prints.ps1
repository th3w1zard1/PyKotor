#!/usr/bin/env pwsh
# Wrapper script for remove_debug_prints.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "remove_debug_prints.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "remove_debug_prints.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
