@echo off
REM Wrapper script for check_kit_completeness.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%check_kit_completeness.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: check_kit_completeness.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
