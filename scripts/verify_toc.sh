#!/bin/bash
# Wrapper script for verify_toc.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/verify_toc.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: verify_toc.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
