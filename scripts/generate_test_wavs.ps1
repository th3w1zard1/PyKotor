#!/usr/bin/env pwsh
# Wrapper script for generate_test_wavs.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "generate_test_wavs.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "generate_test_wavs.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
