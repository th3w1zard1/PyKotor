#!/bin/bash
# Wrapper script for move_markdown_to_docs.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/move_markdown_to_docs.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: move_markdown_to_docs.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
