#!/bin/bash
# Wrapper script for cython_compile_script.py
# Calls the Python script to compile Cython files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/cython_compile_script.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: cython_compile_script.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Call the Python script
exec python3 "$PYTHON_SCRIPT" "$@"
