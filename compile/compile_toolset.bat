@echo off
REM Wrapper script for compile_toolset.ps1
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=!SCRIPT_DIR!compile_toolset.py"
set "PS1_SCRIPT=!SCRIPT_DIR!compile_toolset.ps1"

REM Try Python version first, fall back to PowerShell
if exist "!PYTHON_SCRIPT!" (
    python "!PYTHON_SCRIPT!" %*
    exit /b %ERRORLEVEL%
) else if exist "!PS1_SCRIPT!" (
    if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
        "C:\Program Files\PowerShell\7\pwsh.exe" -File "!PS1_SCRIPT!" %*
    ) else (
        powershell -File "!PS1_SCRIPT!" %*
    )
    exit /b %ERRORLEVEL%
) else (
    echo Error: Neither compile_toolset.py nor compile_toolset.ps1 found >&2
    exit /b 1
)
