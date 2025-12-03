#!/bin/bash
# Wrapper script for convert_pdf_to_markdown.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/convert_pdf_to_markdown.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: convert_pdf_to_markdown.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
