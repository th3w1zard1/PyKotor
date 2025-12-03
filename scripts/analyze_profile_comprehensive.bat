@echo off
REM Wrapper script for analyze_profile_comprehensive.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%analyze_profile_comprehensive.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: analyze_profile_comprehensive.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
