#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "normalize_pythonpath.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "normalize_pythonpath.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
