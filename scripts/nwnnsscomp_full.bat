@echo off
REM Wrapper script for nwnnsscomp_full.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%nwnnsscomp_full.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: nwnnsscomp_full.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
