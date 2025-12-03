#!/usr/bin/env pwsh
# Wrapper script for add_placeholders.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "add_placeholders.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "add_placeholders.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
