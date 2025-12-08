#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/compile_tool.py"
PYTHON_BIN="${pythonExePath:-python}"

echo "Delegating to compile_tool.py with args: $*"
"${PYTHON_BIN}" "${PYTHON_SCRIPT}" "$@"

