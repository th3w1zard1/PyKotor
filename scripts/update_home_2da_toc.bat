@echo off
REM Wrapper script for update_home_2da_toc.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%update_home_2da_toc.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: update_home_2da_toc.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
