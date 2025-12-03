#!/usr/bin/env pwsh
# Wrapper script for generate_scriptdefs.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "generate_scriptdefs.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "generate_scriptdefs.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
