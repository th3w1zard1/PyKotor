@echo off
REM Wrapper script for add_help_tests.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%add_help_tests.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: add_help_tests.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
