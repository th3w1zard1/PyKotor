#!/usr/bin/env pwsh
# Wrapper script for find_localization_strings.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "find_localization_strings.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "find_localization_strings.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
