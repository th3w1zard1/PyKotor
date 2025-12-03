#!/usr/bin/env pwsh
# Wrapper script for update_nss_documentation.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "update_nss_documentation.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "update_nss_documentation.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
