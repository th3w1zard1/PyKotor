#!/bin/bash
# Wrapper script for deps_holopatcher
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/deps_holopatcher.py" ]]; then
    exec python3 "$SCRIPT_DIR/deps_holopatcher.py" "$@"
elif command -v pwsh >/dev/null 2>&1 && [[ -f "$SCRIPT_DIR/deps_holopatcher.ps1" ]]; then
    exec pwsh -File "$SCRIPT_DIR/deps_holopatcher.ps1" "$@"
else
    echo "Error: Neither deps_holopatcher.py nor PowerShell found" >&2
    exit 1
fi
