@echo off
REM Wrapper script for verify_toc.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%verify_toc.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: verify_toc.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
