#!/bin/bash
# Wrapper script for deps_batchpatcher
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try Python version first, fall back to PowerShell
if [[ -f "$SCRIPT_DIR/deps_batchpatcher.py" ]]; then
    exec python3 "$SCRIPT_DIR/deps_batchpatcher.py" "$@"
elif command -v pwsh >/dev/null 2>&1 && [[ -f "$SCRIPT_DIR/deps_batchpatcher.ps1" ]]; then
    exec pwsh -File "$SCRIPT_DIR/deps_batchpatcher.ps1" "$@"
else
    echo "Error: Neither deps_batchpatcher.py nor PowerShell found" >&2
    exit 1
fi
