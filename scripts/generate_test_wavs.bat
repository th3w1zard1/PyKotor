@echo off
REM Wrapper script for generate_test_wavs.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%generate_test_wavs.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: generate_test_wavs.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
