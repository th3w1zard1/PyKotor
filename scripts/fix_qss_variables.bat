@echo off
REM Wrapper script for fix_qss_variables.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%fix_qss_variables.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: fix_qss_variables.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
