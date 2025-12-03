#!/usr/bin/env pwsh
# Wrapper script for parse_nss_to_python.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "parse_nss_to_python.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "parse_nss_to_python.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
