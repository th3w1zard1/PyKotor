#!/bin/bash
# Wrapper script for integrate_vscode_themes.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/integrate_vscode_themes.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: integrate_vscode_themes.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
