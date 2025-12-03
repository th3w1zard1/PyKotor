@echo off
REM Wrapper script for add_placeholders.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%add_placeholders.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: add_placeholders.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
