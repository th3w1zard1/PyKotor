#!/usr/bin/env pwsh
# Wrapper script for cython_compile_script.py
# Calls the Python script to compile Cython files

param(
    [string]$RootDir = "."
)

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "cython_compile_script.py"

if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {
    Write-Error "cython_compile_script.py not found at $pythonScript"
    exit 1
}

# Call the Python script
python $pythonScript
exit $LASTEXITCODE
