#!/usr/bin/env pwsh
# Wrapper script for integrate_vscode_themes.py
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "integrate_vscode_themes.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "integrate_vscode_themes.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE
