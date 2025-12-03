#!/bin/bash
# Wrapper script for extract_gff_generics.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/extract_gff_generics.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: extract_gff_generics.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
