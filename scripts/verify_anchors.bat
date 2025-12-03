@echo off
REM Wrapper script for verify_anchors.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%verify_anchors.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: verify_anchors.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
