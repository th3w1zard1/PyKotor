@echo off
REM Wrapper script for convert_pdf_to_markdown.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%convert_pdf_to_markdown.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: convert_pdf_to_markdown.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
