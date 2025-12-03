#!/usr/bin/env pwsh
# Wrapper script for extract_nss_sections.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "extract_nss_sections.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "extract_nss_sections.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
