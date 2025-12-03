@echo off
REM Wrapper script for generate_dencs_nodes.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%generate_dencs_nodes.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: generate_dencs_nodes.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
