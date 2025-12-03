#!/bin/bash
# Wrapper script for generate_dencs_nodes.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/generate_dencs_nodes.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: generate_dencs_nodes.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
