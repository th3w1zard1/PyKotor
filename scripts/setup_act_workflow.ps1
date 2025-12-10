#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "setup_act_workflow.py"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "setup_act_workflow.py not found at $pythonScript"
    exit 1
}
python $pythonScript $args
exit $LASTEXITCODE

