@echo off
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
if exist "!SCRIPT_DIR!deps_holopatcher.py" (
    python "!SCRIPT_DIR!deps_holopatcher.py" %*
    exit /b %ERRORLEVEL%
) else if exist "!SCRIPT_DIR!deps_holopatcher.ps1" (
    if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
        "C:\Program Files\PowerShell\7\pwsh.exe" -File "!SCRIPT_DIR!deps_holopatcher.ps1" %*
    ) else (
        powershell -File "!SCRIPT_DIR!deps_holopatcher.ps1" %*
    )
    exit /b %ERRORLEVEL%
) else (
    echo Error: Neither deps_holopatcher.py nor deps_holopatcher.ps1 found >&2
    exit /b 1
)
