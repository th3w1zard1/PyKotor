#!/usr/bin/env pwsh
# Wrapper script for analyze_profile_comprehensive.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "analyze_profile_comprehensive.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "analyze_profile_comprehensive.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
