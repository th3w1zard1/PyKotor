#!/usr/bin/env pwsh
# Wrapper script for nwnnsscomp_full.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "nwnnsscomp_full.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "nwnnsscomp_full.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
