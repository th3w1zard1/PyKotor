#!/bin/bash
# Wrapper script for parse_nss_to_python.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/parse_nss_to_python.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: parse_nss_to_python.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
