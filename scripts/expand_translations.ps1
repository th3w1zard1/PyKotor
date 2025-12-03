#!/usr/bin/env pwsh
# Wrapper script for expand_translations.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "expand_translations.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "expand_translations.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
