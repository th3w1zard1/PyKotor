#!/usr/bin/env pwsh
# Wrapper script for check_encryption.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "check_encryption.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "check_encryption.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
