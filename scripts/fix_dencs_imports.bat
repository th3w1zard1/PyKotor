@echo off
REM Wrapper script for fix_dencs_imports.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%fix_dencs_imports.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: fix_dencs_imports.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
