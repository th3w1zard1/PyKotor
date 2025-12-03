@echo off
REM Wrapper script for parse_nss_to_python.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%parse_nss_to_python.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: parse_nss_to_python.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
