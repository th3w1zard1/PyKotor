#!/usr/bin/env pwsh
# Wrapper script for verify_anchors.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "verify_anchors.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "verify_anchors.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
