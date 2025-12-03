#!/bin/bash
# Wrapper script for check_kit_completeness.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/check_kit_completeness.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: check_kit_completeness.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
