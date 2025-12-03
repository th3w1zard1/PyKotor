#!/bin/bash
# Wrapper script for verify_anchors.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/verify_anchors.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: verify_anchors.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
