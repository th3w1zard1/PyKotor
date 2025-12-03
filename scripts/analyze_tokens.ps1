#!/usr/bin/env pwsh
# Wrapper script for analyze_tokens.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "analyze_tokens.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "analyze_tokens.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
