@echo off
REM Wrapper script for find_localization_strings.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%find_localization_strings.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: find_localization_strings.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
