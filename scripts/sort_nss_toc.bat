@echo off
REM Wrapper script for sort_nss_toc.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%sort_nss_toc.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: sort_nss_toc.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
