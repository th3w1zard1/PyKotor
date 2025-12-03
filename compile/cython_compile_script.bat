@echo off
REM Wrapper script for cython_compile_script.py
REM Calls the Python script to compile Cython files

setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%cython_compile_script.py"

if not exist "!PYTHON_SCRIPT!" (
    echo Error: cython_compile_script.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)

REM Call the Python script
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
