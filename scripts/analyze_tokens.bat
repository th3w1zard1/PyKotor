@echo off
REM Wrapper script for analyze_tokens.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%analyze_tokens.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: analyze_tokens.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
