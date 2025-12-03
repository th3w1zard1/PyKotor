#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive profile analysis tool for identifying performance bottlenecks.

.DESCRIPTION
    Wrapper script that calls the Python analyze_profile.py script to analyze
    cProfile output files (.prof) and provides detailed breakdowns of function
    execution times, call counts, and call chains.

.PARAMETER ProfileFile
    Path to the .prof profile file to analyze (optional if using --default-paths).

.PARAMETER Output
    Path to write output file (default: print to stdout).

.PARAMETER TopCumulative
    Number of top functions by cumulative time to show (default: 50).

.PARAMETER TopSelf
    Number of top functions by self time to show (default: 50).

.PARAMETER TopCalls
    Number of top functions by call count to show (default: 30).

.PARAMETER TopCallers
    Number of top callers to show (default: 30).

.PARAMETER TopCallees
    Number of top callees to show (default: 30).

.PARAMETER NoCallers
    Skip callers analysis.

.PARAMETER NoCallees
    Skip callees analysis.

.PARAMETER DefaultPaths
    Try common default profile file paths if ProfileFile not provided.

.EXAMPLE
    .\scripts\analyze_profile.ps1 profile.prof

.EXAMPLE
    .\scripts\analyze_profile.ps1 profile.prof --output analysis.txt

.EXAMPLE
    .\scripts\analyze_profile.ps1 --default-paths
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
    [int]$TopCallers = 30,
    
    [Parameter()]
    [int]$TopCallees = 30,
    
    [Parameter()]
    [switch]$NoCallers,
    
    [Parameter()]
    [switch]$NoCallees,
    
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

if ($TopCumulative -ne 50) {
    $pythonArgs += "--top-cumulative", $TopCumulative
}

if ($TopSelf -ne 50) {
    $pythonArgs += "--top-self", $TopSelf
}

if ($TopCalls -ne 30) {
    $pythonArgs += "--top-calls", $TopCalls
}

if ($TopCallers -ne 30) {
    $pythonArgs += "--top-callers", $TopCallers
}

if ($TopCallees -ne 30) {
    $pythonArgs += "--top-callees", $TopCallees
}

if ($NoCallers) {
    $pythonArgs += "--no-callers"
}

if ($NoCallees) {
    $pythonArgs += "--no-callees"
}

if ($DefaultPaths) {
    $pythonArgs += "--default-paths"
}

# Call the Python script
$scriptPath = Join-Path $PSScriptRoot "analyze_profile.py"
python $scriptPath $pythonArgs
