@echo off
REM Comprehensive profile analysis tool for identifying performance bottlenecks.
REM
REM Wrapper script that calls the Python analyze_profile.py script to analyze
REM cProfile output files (.prof) and provides detailed breakdowns of function
REM execution times, call counts, and call chains.

setlocal enabledelayedexpansion

REM Default values
set "PROFILE_FILE="
set "OUTPUT="
set "TOP_CUMULATIVE=50"
set "TOP_SELF=50"
set "TOP_CALLS=30"
set "TOP_CALLERS=30"
set "TOP_CALLEES=30"
set "NO_CALLERS=false"
set "NO_CALLEES=false"
set "DEFAULT_PATHS=false"

REM Parse arguments
:parse_args
if "%~1"=="" goto end_parse
if /i "%~1"=="-o" (
    set "OUTPUT=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--output" (
    set "OUTPUT=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--top-cumulative" (
    set "TOP_CUMULATIVE=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--top-self" (
    set "TOP_SELF=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--top-calls" (
    set "TOP_CALLS=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--top-callers" (
    set "TOP_CALLERS=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--top-callees" (
    set "TOP_CALLEES=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--no-callers" (
    set "NO_CALLERS=true"
    shift
    goto parse_args
)
if /i "%~1"=="--no-callees" (
    set "NO_CALLEES=true"
    shift
    goto parse_args
)
if /i "%~1"=="--default-paths" (
    set "DEFAULT_PATHS=true"
    shift
    goto parse_args
)
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
if "!PROFILE_FILE!"=="" (
    set "PROFILE_FILE=%~1"
    shift
    goto parse_args
)
echo Error: Unexpected argument: %~1 >&2
exit /b 1

:show_help
echo Usage: %~nx0 [PROFILE_FILE] [OPTIONS]
echo.
echo Options:
echo   -o, --output PATH          Path to write output file (default: print to stdout)
echo   --top-cumulative N         Number of top functions by cumulative time (default: 50)
echo   --top-self N               Number of top functions by self time (default: 50)
echo   --top-calls N              Number of top functions by call count (default: 30)
echo   --top-callers N            Number of top callers to show (default: 30)
echo   --top-callees N            Number of top callees to show (default: 30)
echo   --no-callers               Skip callers analysis
echo   --no-callees               Skip callees analysis
echo   --default-paths            Try common default profile file paths
echo   -h, --help                 Show this help message
exit /b 0

:end_parse

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "ANALYZE_PROFILE_SCRIPT=%SCRIPT_DIR%analyze_profile.py"

if not exist "!ANALYZE_PROFILE_SCRIPT!" (
    echo Error: analyze_profile.py not found at !ANALYZE_PROFILE_SCRIPT! >&2
    exit /b 1
)

REM Build argument list
set "PYTHON_ARGS="

if not "!PROFILE_FILE!"=="" (
    set "PYTHON_ARGS=!PYTHON_ARGS! !PROFILE_FILE!"
)

if not "!OUTPUT!"=="" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --output !OUTPUT!"
)

if not "!TOP_CUMULATIVE!"=="50" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --top-cumulative !TOP_CUMULATIVE!"
)

if not "!TOP_SELF!"=="50" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --top-self !TOP_SELF!"
)

if not "!TOP_CALLS!"=="30" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --top-calls !TOP_CALLS!"
)

if not "!TOP_CALLERS!"=="30" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --top-callers !TOP_CALLERS!"
)

if not "!TOP_CALLEES!"=="30" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --top-callees !TOP_CALLEES!"
)

if "!NO_CALLERS!"=="true" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --no-callers"
)

if "!NO_CALLEES!"=="true" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --no-callees"
)

if "!DEFAULT_PATHS!"=="true" (
    set "PYTHON_ARGS=!PYTHON_ARGS! --default-paths"
)

REM Call the Python script
python "!ANALYZE_PROFILE_SCRIPT!"!PYTHON_ARGS!
exit /b %ERRORLEVEL%
