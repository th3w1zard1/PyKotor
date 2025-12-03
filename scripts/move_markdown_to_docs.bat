@echo off
REM Wrapper script for move_markdown_to_docs.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%move_markdown_to_docs.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: move_markdown_to_docs.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
