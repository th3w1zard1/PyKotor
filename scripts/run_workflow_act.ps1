#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run GitHub Actions workflow locally using act.

.DESCRIPTION
    This script runs the publish_pykotor.yml workflow locally using act.
    It sets up the necessary environment and event files, then executes the workflow.

.PARAMETER Workflow
    Path to the workflow file. Default: .github/workflows/publish_pykotor.yml

.PARAMETER Job
    Specific job to run (optional). If not specified, runs all jobs.

.PARAMETER Event
    Event type to trigger. Default: workflow_dispatch

.PARAMETER List
    List available jobs in the workflow without running.

.PARAMETER ActVerbose
    Enable verbose output from act.

.PARAMETER DryRun
    Print the act command without executing it.

.EXAMPLE
    .\scripts\run_workflow_act.ps1

.EXAMPLE
    .\scripts\run_workflow_act.ps1 -Job "detect-tools"

.EXAMPLE
    .\scripts\run_workflow_act.ps1 -List

.EXAMPLE
    .\scripts\run_workflow_act.ps1 -ActVerbose -DryRun
#>

[CmdletBinding()]
param(
    [string]$Workflow = ".github/workflows/publish_pykotor.yml",
    [string]$Job = "",
    [ValidateSet("workflow_dispatch", "schedule", "push")]
    [string]$Event = "workflow_dispatch",
    [switch]$List,
    [switch]$ActVerbose,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Check if we're in the repo root
if (-not (Test-Path $Workflow)) {
    Write-Error "Workflow file not found: $Workflow"
    Write-Host "This script must be run from the repository root."
    exit 1
}

# Check if act is installed
if (-not (Get-Command act -ErrorAction SilentlyContinue)) {
    Write-Error "act is not installed. Please install it first:"
    Write-Host "  Windows: choco install act-cli"
    Write-Host "  macOS: brew install act"
    Write-Host "  Linux: See https://github.com/nektos/act#installation"
    Write-Host ""
    Write-Host "Or run: python scripts/setup_act_workflow.py --install-act"
    exit 1
}

Write-Host "========================================="
Write-Host "Running GitHub Actions Workflow with act"
Write-Host "========================================="
Write-Host "Workflow: $Workflow"
Write-Host "Event: $Event"
if ($Job) {
    Write-Host "Job: $Job"
}
Write-Host "========================================="
Write-Host ""

# Check act version
$actVersion = act --version 2>&1
Write-Host "act version: $actVersion"
Write-Host ""

# Create event file for workflow_dispatch
$eventFile = ".github/workflows/event.json"
if (-not (Test-Path ".github/workflows")) {
    New-Item -ItemType Directory -Path ".github/workflows" -Force | Out-Null
}

if ($Event -eq "workflow_dispatch") {
    $eventContent = @{
        inputs = @{}
    } | ConvertTo-Json -Depth 10
    
    $eventContent | Out-File -FilePath $eventFile -Encoding UTF8 -NoNewline
    Write-Host "Created event file: $eventFile"
    Write-Host ""
}

# List jobs if requested
if ($List) {
    Write-Host "Listing available jobs..."
    Write-Host ""
    $actCommand = "act -l -W $Workflow"
    if ($Event -eq "workflow_dispatch" -and (Test-Path $eventFile)) {
        $actCommand += " -e $eventFile"
    }
    Write-Host "Command: $actCommand"
    Write-Host ""
    
    if (-not $DryRun) {
        if ($Event -eq "workflow_dispatch" -and (Test-Path $eventFile)) {
            act -l -W $Workflow -e $eventFile
        }
        else {
            act -l -W $Workflow
        }
        exit $LASTEXITCODE
    }
    else {
        exit 0
    }
}

# Build act command
# Act uses the event name as the first argument, then flags
$actArgs = @()

# Add event name (workflow_dispatch)
$actArgs += $Event

# Add workflow file
$actArgs += @("-W", $Workflow)

# Add event file if it exists
if ($Event -eq "workflow_dispatch" -and (Test-Path $eventFile)) {
    $actArgs += @("-e", $eventFile)
}

# Add specific job if specified
if ($Job) {
    $actArgs += @("-j", $Job)
    
    # For build job, enable test mode to limit matrix combinations
    # This makes testing much faster (1 tool, 1 OS, 1 Python version, 1 architecture)
    if ($Job -eq "build") {
        $env:ACT_TEST_MODE = "true"
        # Optionally specify a tool to test (defaults to first tool)
        # $env:ACT_TEST_TOOL = "BatchPatcher"
        Write-Host "Test mode enabled: limiting matrix to 1 tool, 1 OS, 1 Python version, 1 architecture" -ForegroundColor Cyan
    }
}

# Add verbose flag
if ($ActVerbose) {
    $actArgs += @("-v")
}

# Add platform-specific runner
# Act needs to know which runner image to use
# Note: Act simulates Windows/macOS in Linux containers, so all jobs run on Linux
# The workflow installs PowerShell on non-Windows (via install_powershell.sh) before using it
# We map all platforms to ubuntu-latest so PowerShell gets installed properly
# Use --pull=false to avoid rate limits if image is already cached
$actArgs += @("-P", "ubuntu-latest=catthehacker/ubuntu:act-latest")
$actArgs += @("-P", "windows-latest=catthehacker/ubuntu:act-latest")
$actArgs += @("-P", "macos-latest=catthehacker/ubuntu:act-latest")
$actArgs += @("--pull=false")

# Add --rm to automatically clean up containers/volumes after failure
# This helps avoid Docker volume cleanup issues with submodules
$actArgs += @("--rm")

# Use --bind to bind working directory instead of copying (avoids vendor submodule issues)
$actArgs += @("--bind")

# Set environment variables to help act work better
# ACTIONS_RUNTIME_TOKEN is needed for artifact uploads (but act doesn't fully support this)
# We'll set a dummy value to prevent errors
$env:ACTIONS_RUNTIME_TOKEN = "dummy-token-for-act"
$env:ACTIONS_RUNTIME_URL = "http://localhost:8080"

# For build job, enable test mode to dramatically speed up testing
# This limits matrix to: 1 tool, 1 OS (ubuntu-latest), 1 Python version (3.13), 1 architecture (x64)
# This reduces matrix from ~288 combinations (8 tools × 3 OS × 6 Python × 2 arch) to just 1
if ($Job -eq "build") {
    # Pass environment variable to act using --env flag
    $actArgs += @("--env", "ACT_TEST_MODE=true")
    Write-Host "Test mode enabled: limiting to 1 tool, ubuntu-latest, Python 3.13, x64" -ForegroundColor Cyan
    Write-Host "This reduces matrix from ~288 combinations to just 1" -ForegroundColor Cyan
    Write-Host ""
}

# Build the full command
$actCommand = "act $($actArgs -join ' ')"

Write-Host "Command: $actCommand"
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would execute: $actCommand"
    exit 0
}

# Note about act limitations
Write-Host "Note: act has limitations with complex workflows:" -ForegroundColor Yellow
Write-Host "  - Matrix builds may not work as expected" -ForegroundColor Yellow
Write-Host "  - Some actions may not be fully supported" -ForegroundColor Yellow
Write-Host "  - Windows/macOS runners are simulated" -ForegroundColor Yellow
Write-Host "  - Artifact uploads/downloads may not work" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
Start-Sleep -Seconds 5
Write-Host ""

# Run act with timeout (2 minutes for build job, 30 seconds for others)
Write-Host "Executing workflow with act..."
Write-Host ""

$timeoutSeconds = if ($Job -eq "build") { 120 } else { 30 }
Write-Host "Timeout set to $timeoutSeconds seconds" -ForegroundColor Cyan
Write-Host ""

try {
    # Run act directly but with a timeout wrapper
    $actProcess = Start-Process -FilePath "act" -ArgumentList $actArgs -PassThru -NoNewWindow
    
    $completed = $actProcess.WaitForExit($timeoutSeconds * 1000)
    
    if (-not $completed) {
        Write-Host "Workflow execution exceeded $timeoutSeconds second timeout!" -ForegroundColor Red
        Write-Host "Killing act process..." -ForegroundColor Yellow
        $actProcess.Kill()
        $actProcess.WaitForExit(5000)
        Write-Host "This indicates a bottleneck - check matrix combinations and workflow steps" -ForegroundColor Yellow
        Write-Host "Test mode should limit to 1 combination - verify ACT_TEST_MODE is set correctly" -ForegroundColor Yellow
        exit 1
    }
    
    $exitCode = $actProcess.ExitCode
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "========================================="
        Write-Host "Workflow completed successfully!" -ForegroundColor Green
        Write-Host "========================================="
    }
    else {
        Write-Host ""
        Write-Host "========================================="
        Write-Host "Workflow completed with errors (exit code: $exitCode)" -ForegroundColor Yellow
        Write-Host "========================================="
        Write-Host ""
        Write-Host "Note: Some errors may be expected due to act limitations." -ForegroundColor Yellow
        Write-Host "Check the output above for specific issues." -ForegroundColor Yellow
    }
    
    exit $exitCode
}
catch {
    Write-Host ""
    Write-Host "========================================="
    Write-Host "Error running workflow:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "========================================="
    exit 1
}

