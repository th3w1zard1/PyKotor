#!/bin/bash
# Wrapper script for update_2da_main.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/update_2da_main.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: update_2da_main.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
