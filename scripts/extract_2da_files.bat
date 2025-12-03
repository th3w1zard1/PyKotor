@echo off
REM Wrapper script for extract_2da_files.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%extract_2da_files.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: extract_2da_files.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
