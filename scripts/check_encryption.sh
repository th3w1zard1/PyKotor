#!/bin/bash
# Wrapper script for check_encryption.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/check_encryption.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: check_encryption.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
