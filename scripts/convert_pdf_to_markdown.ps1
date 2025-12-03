#!/usr/bin/env pwsh
# Wrapper script for convert_pdf_to_markdown.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "convert_pdf_to_markdown.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "convert_pdf_to_markdown.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
