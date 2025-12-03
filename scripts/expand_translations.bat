@echo off
REM Wrapper script for expand_translations.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%expand_translations.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: expand_translations.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
