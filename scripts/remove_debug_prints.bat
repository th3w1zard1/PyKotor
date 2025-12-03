@echo off
REM Wrapper script for remove_debug_prints.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%remove_debug_prints.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: remove_debug_prints.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
