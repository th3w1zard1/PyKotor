#!/bin/bash
# Wrapper script for expand_translations.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/expand_translations.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: expand_translations.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
