#!/bin/bash
# Wrapper script for debug_dlg_serialization.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/debug_dlg_serialization.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: debug_dlg_serialization.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
