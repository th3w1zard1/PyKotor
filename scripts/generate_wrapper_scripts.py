#!/usr/bin/env python3
"""Generate wrapper scripts (.ps1, .sh, .bat) for all Python scripts.

This script scans for Python files and generates wrapper scripts in PowerShell,
shell, and batch formats.
"""

from __future__ import annotations

import os
from pathlib import Path


def generate_ps1_wrapper(python_script: Path) -> str:
    """Generate PowerShell wrapper script."""
    script_name = python_script.stem
    return f"""#!/usr/bin/env pwsh
# Wrapper script for {python_script.name}
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "{python_script.name}"
if (-not (Test-Path -LiteralPath $pythonScript -ErrorAction SilentlyContinue)) {{
    Write-Error "{python_script.name} not found at $pythonScript"
    exit 1
}}
python $pythonScript $args
exit $LASTEXITCODE
"""


def generate_sh_wrapper(python_script: Path) -> str:
    """Generate shell script wrapper."""
    script_name = python_script.stem
    return f"""#!/bin/bash
# Wrapper script for {python_script.name}
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/{python_script.name}"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: {python_script.name} not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
"""


def generate_bat_wrapper(python_script: Path) -> str:
    """Generate batch file wrapper."""
    script_name = python_script.stem
    return f"""@echo off
REM Wrapper script for {python_script.name}
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%{python_script.name}"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: {python_script.name} not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
"""


def main() -> None:
    """Main entry point."""
    script_dir = Path(__file__).parent
    compile_dir = script_dir.parent / "compile"

    # Find all Python files that need wrappers
    python_files = []
    
    # Scripts directory
    for py_file in script_dir.glob("*.py"):
        if py_file.name.startswith("test_") or py_file.name.startswith("generate_wrapper"):
            continue
        python_files.append(py_file)
    
    # Compile directory
    if compile_dir.exists():
        for py_file in compile_dir.glob("*.py"):
            python_files.append(py_file)

    # Generate wrappers
    generated = 0
    for py_file in python_files:
        base_name = py_file.stem
        
        # Generate .ps1
        ps1_file = py_file.with_suffix(".ps1")
        if not ps1_file.exists():
            ps1_file.write_text(generate_ps1_wrapper(py_file), encoding="utf-8")
            print(f"Generated: {ps1_file}")
            generated += 1
        
        # Generate .sh
        sh_file = py_file.with_suffix(".sh")
        if not sh_file.exists():
            sh_file.write_text(generate_sh_wrapper(py_file), encoding="utf-8")
            print(f"Generated: {sh_file}")
            generated += 1
        
        # Generate .bat
        bat_file = py_file.with_suffix(".bat")
        if not bat_file.exists():
            bat_file.write_text(generate_bat_wrapper(py_file), encoding="utf-8")
            print(f"Generated: {bat_file}")
            generated += 1
    
    print(f"\nGenerated {generated} wrapper scripts.")


if __name__ == "__main__":
    main()
