#!/bin/bash
# Wrapper script for check_pypi_deps.py
# Calls the Python script to check PyPI package dependencies and metadata

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/check_pypi_deps.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: check_pypi_deps.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Pass all arguments to the Python script
exec python3 "$PYTHON_SCRIPT" "$@"
