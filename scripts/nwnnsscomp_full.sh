#!/bin/bash
# Wrapper script for nwnnsscomp_full.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/nwnnsscomp_full.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: nwnnsscomp_full.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
