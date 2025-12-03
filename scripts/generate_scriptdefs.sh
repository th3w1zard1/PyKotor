#!/bin/bash
# Wrapper script for generate_scriptdefs.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/generate_scriptdefs.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: generate_scriptdefs.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
