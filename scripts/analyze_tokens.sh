#!/bin/bash
# Wrapper script for analyze_tokens.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/analyze_tokens.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: analyze_tokens.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
