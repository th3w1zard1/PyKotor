@echo off
REM Wrapper script for deps_batchpatcher
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"

REM Try Python version first, fall back to PowerShell
if exist "!SCRIPT_DIR!deps_batchpatcher.py" (
    python "!SCRIPT_DIR!deps_batchpatcher.py" %*
    exit /b %ERRORLEVEL%
) else if exist "!SCRIPT_DIR!deps_batchpatcher.ps1" (
    if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
        "C:\Program Files\PowerShell\7\pwsh.exe" -File "!SCRIPT_DIR!deps_batchpatcher.ps1" %*
        exit /b %ERRORLEVEL%
    ) else (
        powershell -File "!SCRIPT_DIR!deps_batchpatcher.ps1" %*
        exit /b %ERRORLEVEL%
    )
) else (
    echo Error: Neither deps_batchpatcher.py nor deps_batchpatcher.ps1 found >&2
    exit /b 1
)
