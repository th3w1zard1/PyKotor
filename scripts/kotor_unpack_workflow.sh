#!/bin/bash
# Wrapper script for kotor_unpack_workflow.ps1
set -euo pipefail
SCRIPT_DIR="${(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
PYTHON_SCRIPT="$SCRIPT_DIR/kotor_unpack_workflow.py"
PS1_SCRIPT="$SCRIPT_DIR/kotor_unpack_workflow.ps1"

# Try Python version first, fall back to PowerShell
if [[ -f "$PYTHON_SCRIPT" ]]; then
    exec python3 "$PYTHON_SCRIPT" "$@"
elif command -v pwsh >/dev/null 2>&1 && [[ -f "$PS1_SCRIPT" ]]; then
    exec pwsh -File "$PS1_SCRIPT" "$@"
else
    echo "Error: Neither kotor_unpack_workflow.py nor PowerShell found" >&2
    exit 1
fi
