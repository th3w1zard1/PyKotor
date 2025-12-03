#!/bin/bash
# Wrapper script for remove_debug_prints.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/remove_debug_prints.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: remove_debug_prints.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
