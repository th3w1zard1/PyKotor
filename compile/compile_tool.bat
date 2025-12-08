@echo off
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%compile_tool.py"
set "PYTHON_BIN=%pythonExePath%"
if "%PYTHON_BIN%"=="" set "PYTHON_BIN=python"

echo Delegating to compile_tool.py with args: %*
"%PYTHON_BIN%" "%PYTHON_SCRIPT%" %*
exit /b %ERRORLEVEL%

