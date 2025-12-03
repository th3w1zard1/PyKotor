#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "extract_lyt_doorhooks.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "extract_lyt_doorhooks.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
