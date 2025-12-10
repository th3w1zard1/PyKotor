# Wrapper script for generate_scriptdefs_csharp.py
$ErrorActionPreference = "Stop"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PYTHON_SCRIPT = Join-Path $SCRIPT_DIR "generate_scriptdefs_csharp.py"

if (-not (Test-Path $PYTHON_SCRIPT)) {
    Write-Error "Error: generate_scriptdefs_csharp.py not found at $PYTHON_SCRIPT"
    exit 1
}

python $PYTHON_SCRIPT $args
exit $LASTEXITCODE

