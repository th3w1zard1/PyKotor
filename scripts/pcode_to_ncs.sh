#!/bin/bash
# Wrapper script for pcode_to_ncs.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/pcode_to_ncs.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: pcode_to_ncs.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
