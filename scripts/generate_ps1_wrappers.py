#!/usr/bin/env python3
"""Generate wrapper scripts for PowerShell scripts.

Creates .py, .sh, and .bat wrapper scripts for all .ps1 files.
"""

from __future__ import annotations

import sys
from pathlib import Path


def generate_sh_wrapper(ps1_file: Path) -> str:
    """Generate shell script wrapper."""
    name = ps1_file.stem
    ps1_name = ps1_file.name
    return f"""#!/bin/bash
# Wrapper script for {ps1_name}
set -euo pipefail
SCRIPT_DIR="${{(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)}}"
PYTHON_SCRIPT="$SCRIPT_DIR/{name}.py"
PS1_SCRIPT="$SCRIPT_DIR/{ps1_name}"

# Try Python version first, fall back to PowerShell
if [[ -f "$PYTHON_SCRIPT" ]]; then
    exec python3 "$PYTHON_SCRIPT" "$@"
elif command -v pwsh >/dev/null 2>&1 && [[ -f "$PS1_SCRIPT" ]]; then
    exec pwsh -File "$PS1_SCRIPT" "$@"
else
    echo "Error: Neither {name}.py nor PowerShell found" >&2
    exit 1
fi
"""


def generate_bat_wrapper(ps1_file: Path) -> str:
    """Generate batch file wrapper."""
    name = ps1_file.stem
    return f"""@echo off
REM Wrapper script for {ps1_file.name}
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=!SCRIPT_DIR!{name}.py"
set "PS1_SCRIPT=!SCRIPT_DIR!{ps1_file.name}"

REM Try Python version first, fall back to PowerShell
if exist "!PYTHON_SCRIPT!" (
    python "!PYTHON_SCRIPT!" %*
    exit /b %ERRORLEVEL%
) else if exist "!PS1_SCRIPT!" (
    if exist "C:\\Program Files\\PowerShell\\7\\pwsh.exe" (
        "C:\\Program Files\\PowerShell\\7\\pwsh.exe" -File "!PS1_SCRIPT!" %*
    ) else (
        powershell -File "!PS1_SCRIPT!" %*
    )
    exit /b %ERRORLEVEL%
) else (
    echo Error: Neither {name}.py nor {ps1_file.name} found >&2
    exit /b 1
)
"""


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        target_dirs = [Path(p) for p in sys.argv[1:]]
    else:
        target_dirs = [Path("compile"), Path("scripts")]
    
    generated = 0
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        
        for ps1_file in target_dir.rglob("*.ps1"):
            # Skip workflow subdirectory for now (those are complex)
            if "workflow" in ps1_file.parts:
                continue
            
            # Generate .sh
            sh_file = ps1_file.with_suffix(".sh")
            if not sh_file.exists():
                sh_file.write_text(generate_sh_wrapper(ps1_file), encoding="utf-8")
                print(f"Generated: {sh_file}")
                generated += 1
            
            # Generate .bat
            bat_file = ps1_file.with_suffix(".bat")
            if not bat_file.exists():
                bat_file.write_text(generate_bat_wrapper(ps1_file), encoding="utf-8")
                print(f"Generated: {bat_file}")
                generated += 1
    
    print(f"\nGenerated {generated} wrapper scripts.")


if __name__ == "__main__":
    main()
