@echo off
REM Wrapper script for check_pypi_deps.py
REM Calls the Python script to check PyPI package dependencies and metadata

setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%check_pypi_deps.py"

if not exist "!PYTHON_SCRIPT!" (
    echo Error: check_pypi_deps.py not found at !PYTHON_SCRIPT! >&2
    exit /b 1
)

REM Pass all arguments to the Python script
python "!PYTHON_SCRIPT!" %*
exit /b %ERRORLEVEL%
