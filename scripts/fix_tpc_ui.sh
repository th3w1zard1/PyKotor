#!/bin/bash
# Wrapper script for fix_tpc_ui.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/fix_tpc_ui.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: fix_tpc_ui.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
