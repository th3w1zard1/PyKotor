#!/usr/bin/env pwsh
# Wrapper script for move_markdown_to_docs.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "move_markdown_to_docs.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "move_markdown_to_docs.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
