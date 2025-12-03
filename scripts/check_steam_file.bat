@echo off
REM Wrapper script for check_steam_file.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%check_steam_file.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: check_steam_file.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
