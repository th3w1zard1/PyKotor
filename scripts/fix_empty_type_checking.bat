@echo off
REM Wrapper script for fix_empty_type_checking.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%fix_empty_type_checking.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: fix_empty_type_checking.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
