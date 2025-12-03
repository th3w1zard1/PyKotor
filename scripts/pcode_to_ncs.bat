@echo off
REM Wrapper script for pcode_to_ncs.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%pcode_to_ncs.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: pcode_to_ncs.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
