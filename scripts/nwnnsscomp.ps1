#!/usr/bin/env pwsh
# Wrapper script for nwnnsscomp.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "nwnnsscomp.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "nwnnsscomp.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
