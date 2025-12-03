#!/usr/bin/env pwsh
# Wrapper script for extract_gff_generics.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "extract_gff_generics.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "extract_gff_generics.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
