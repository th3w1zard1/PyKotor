@echo off
REM Wrapper script for check_encryption.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%check_encryption.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: check_encryption.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
