#!/usr/bin/env pwsh
# Wrapper script for pcode_to_ncs.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "pcode_to_ncs.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "pcode_to_ncs.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
