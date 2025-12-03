#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Analyze cProfile output files to identify performance bottlenecks.

.DESCRIPTION
    Wrapper script that calls the Python analyze_profile.py script to analyze
    cProfile output files (.prof) and identify performance bottlenecks in tests
    or application code.

.PARAMETER ProfileFile
    Path to the .prof profile file to analyze. If not provided, will try common default paths.

.PARAMETER Output
    Path to write output file (default: print to stdout).

.PARAMETER TopCumulative
    Number of top functions by cumulative time to show (default: 50).

.PARAMETER TopSelf
    Number of top functions by self time to show (default: 50).

.PARAMETER TopCalls
    Number of top functions by call count to show (default: 30).

.PARAMETER DefaultPaths
    Try common default profile file paths if ProfileFile not provided.

.EXAMPLE
    .\scripts\analyze_cprofile.ps1 tests\cProfile\test_component_equivalence_20251203_160047.prof

.EXAMPLE
    .\scripts\analyze_cprofile.ps1 profile.prof -Output analysis.txt

.EXAMPLE
    .\scripts\analyze_cprofile.ps1 -DefaultPaths
#>
param(
    [Parameter(Position=0)]
    [string]$ProfileFile,
    
    [Parameter()]
    [string]$Output,
    
    [Parameter()]
    [int]$TopCumulative = 50,
    
    [Parameter()]
    [int]$TopSelf = 50,
    
    [Parameter()]
    [int]$TopCalls = 30,
    
    [Parameter()]
    [switch]$DefaultPaths
)

$ErrorActionPreference = "Stop"

# Build argument list for Python script
$pythonArgs = @()

if ($ProfileFile) {
    $pythonArgs += $ProfileFile
}

if ($Output) {
    $pythonArgs += "--output", $Output
}

if ($TopCumulative) {
    $pythonArgs += "--top-cumulative", $TopCumulative
}

if ($TopSelf) {
    $pythonArgs += "--top-self", $TopSelf
}

if ($TopCalls) {
    $pythonArgs += "--top-calls", $TopCalls
}

if ($DefaultPaths) {
    $pythonArgs += "--default-paths"
}

# Call the Python script
$scriptPath = Join-Path $PSScriptRoot "analyze_profile.py"
python $scriptPath $pythonArgs

