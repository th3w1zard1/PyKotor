#!/bin/bash
# Wrapper script for analyze_profile_comprehensive.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/analyze_profile_comprehensive.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: analyze_profile_comprehensive.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec python3 "$PYTHON_SCRIPT" "$@"
