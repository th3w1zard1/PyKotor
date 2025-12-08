#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/deps_tool.py"
PYTHON_BIN="${pythonExePath:-python}"

echo "Delegating to deps_tool.py with args: $*"
"${PYTHON_BIN}" "${PYTHON_SCRIPT}" "$@"

