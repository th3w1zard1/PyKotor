@echo off
REM Wrapper script for update_2da_main.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%update_2da_main.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: update_2da_main.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
