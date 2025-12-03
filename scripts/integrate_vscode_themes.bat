@echo off
REM Wrapper script for integrate_vscode_themes.py
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%integrate_vscode_themes.py"
if not exist "!PYTHON_SCRIPT!" (
    echo Error: integrate_vscode_themes.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
