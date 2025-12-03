#!/usr/bin/env pwsh
# Wrapper script for sort_nss_toc.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "sort_nss_toc.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "sort_nss_toc.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
