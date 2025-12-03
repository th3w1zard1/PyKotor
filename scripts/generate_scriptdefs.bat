@echo off
REM Wrapper script for generate_scriptdefs.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%generate_scriptdefs.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: generate_scriptdefs.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
