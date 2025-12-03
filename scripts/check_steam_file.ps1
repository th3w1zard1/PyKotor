#!/usr/bin/env pwsh
# Wrapper script for check_steam_file.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "check_steam_file.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "check_steam_file.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
