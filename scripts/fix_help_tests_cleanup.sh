#!/bin/bash
# Wrapper script for fix_help_tests_cleanup.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/fix_help_tests_cleanup.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: fix_help_tests_cleanup.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
