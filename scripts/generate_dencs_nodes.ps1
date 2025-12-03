#!/usr/bin/env pwsh
# Wrapper script for generate_dencs_nodes.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "generate_dencs_nodes.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "generate_dencs_nodes.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
