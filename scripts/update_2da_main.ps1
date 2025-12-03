#!/usr/bin/env pwsh
# Wrapper script for update_2da_main.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "update_2da_main.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "update_2da_main.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
