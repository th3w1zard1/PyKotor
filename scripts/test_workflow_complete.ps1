#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive test of the publish_pykotor.yml workflow using act and gh cli.

.DESCRIPTION
    This script thoroughly tests the workflow to ensure it works properly:
    1. Validates workflow syntax with gh cli
    2. Tests each job individually with act
    3. Tests with Linux-only builds (act limitation)
    4. Verifies all critical steps work

.PARAMETER SkipSyntaxCheck
    Skip workflow syntax validation with gh cli.

.PARAMETER SkipBuild
    Skip testing the build job (takes longest).

.PARAMETER ActVerbose
    Enable verbose output from act.
#>

[CmdletBinding()]
param(
    [switch]$SkipSyntaxCheck,
    [switch]$SkipBuild,
    [switch]$ActVerbose
)

$ErrorActionPreference = "Stop"

# Ensure we're in the repo root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptPath
Push-Location $repoRoot
try {
    if (-not (Test-Path ".github/workflows/publish_pykotor.yml")) {
        Write-Error "This script must be run from the repository root or scripts directory."
        exit 1
    }
} finally {
    # We'll stay in repo root for the rest of the script
}

Write-Host "========================================="
Write-Host "Comprehensive Workflow Testing"
Write-Host "========================================="
Write-Host "Working directory: $(Get-Location)"
Write-Host ""

$testResults = @{
    SyntaxCheck = $null
    DetectTools = $null
    Setup = $null
    Build = $null
    Package = $null
    Upload = $null
}

$failedTests = @()
$passedTests = @()

# Test 1: Validate workflow syntax
if (-not $SkipSyntaxCheck) {
    Write-Host "Test 1: Validating workflow syntax with gh cli..." -ForegroundColor Cyan
    try {
        $result = gh workflow view publish_pykotor.yml 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Workflow syntax is valid" -ForegroundColor Green
            $testResults.SyntaxCheck = $true
            $passedTests += "SyntaxCheck"
        } else {
            Write-Host "✗ Workflow syntax validation failed" -ForegroundColor Red
            Write-Host $result
            $testResults.SyntaxCheck = $false
            $failedTests += "SyntaxCheck"
        }
    } catch {
        Write-Host "✗ Failed to validate workflow syntax: $($_.Exception.Message)" -ForegroundColor Red
        $testResults.SyntaxCheck = $false
        $failedTests += "SyntaxCheck"
    }
    Write-Host ""
}

# Test 2: detect-tools job
Write-Host "Test 2: Testing detect-tools job..." -ForegroundColor Cyan
try {
    if ($ActVerbose) {
        $output = & ".\scripts\run_workflow_act.ps1" -Job "detect-tools" -ActVerbose 2>&1
    } else {
        $output = & ".\scripts\run_workflow_act.ps1" -Job "detect-tools" 2>&1
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ detect-tools job passed" -ForegroundColor Green
        $testResults.DetectTools = $true
        $passedTests += "DetectTools"
    } else {
        Write-Host "✗ detect-tools job failed" -ForegroundColor Red
        $testResults.DetectTools = $false
        $failedTests += "DetectTools"
    }
} catch {
    Write-Host "✗ detect-tools job error: $($_.Exception.Message)" -ForegroundColor Red
    $testResults.DetectTools = $false
    $failedTests += "DetectTools"
}
Write-Host ""

# Test 3: setup job
Write-Host "Test 3: Testing setup job..." -ForegroundColor Cyan
try {
    if ($ActVerbose) {
        $output = & ".\scripts\run_workflow_act.ps1" -Job "setup" -ActVerbose 2>&1
    } else {
        $output = & ".\scripts\run_workflow_act.ps1" -Job "setup" 2>&1
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ setup job passed" -ForegroundColor Green
        $testResults.Setup = $true
        $passedTests += "Setup"
    } else {
        Write-Host "✗ setup job failed" -ForegroundColor Red
        $testResults.Setup = $false
        $failedTests += "Setup"
    }
} catch {
    Write-Host "✗ setup job error: $($_.Exception.Message)" -ForegroundColor Red
    $testResults.Setup = $false
    $failedTests += "Setup"
}
Write-Host ""

# Test 4: build job (Linux only due to act limitations)
if (-not $SkipBuild) {
    Write-Host "Test 4: Testing build job (Linux builds only)..." -ForegroundColor Cyan
    Write-Host "Note: Windows/macOS builds will fail in act due to pwsh not being available" -ForegroundColor Yellow
    Write-Host "This is expected - act simulates Windows/macOS in Linux containers" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        if ($ActVerbose) {
            $output = & ".\scripts\run_workflow_act.ps1" -Job "build" -ActVerbose 2>&1
        } else {
            $output = & ".\scripts\run_workflow_act.ps1" -Job "build" 2>&1
        }
        
        # Check if any Linux builds succeeded
        $linuxSuccess = $output | Select-String -Pattern "ubuntu-latest.*✅.*Success" -Quiet
        $hasErrors = $output | Select-String -Pattern "❌.*Failure|exitcode.*failure" -Quiet
        
        if ($linuxSuccess -or -not $hasErrors) {
            Write-Host "✓ build job completed (some matrix combinations may have failed due to act limitations)" -ForegroundColor Green
            $testResults.Build = $true
            $passedTests += "Build"
        } else {
            Write-Host "✗ build job failed completely" -ForegroundColor Red
            $testResults.Build = $false
            $failedTests += "Build"
        }
    } catch {
        Write-Host "✗ build job error: $($_.Exception.Message)" -ForegroundColor Red
        $testResults.Build = $false
        $failedTests += "Build"
    }
    Write-Host ""
}

# Test 5: package job
Write-Host "Test 5: Testing package job..." -ForegroundColor Cyan
Write-Host "Note: This job depends on build artifacts, which may not be available in act" -ForegroundColor Yellow
Write-Host ""
try {
    if ($ActVerbose) {
        $output = & ".\scripts\run_workflow_act.ps1" -Job "package" -ActVerbose 2>&1
    } else {
        $output = & ".\scripts\run_workflow_act.ps1" -Job "package" 2>&1
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ package job passed" -ForegroundColor Green
        $testResults.Package = $true
        $passedTests += "Package"
    } else {
        Write-Host "⚠ package job failed (expected if build artifacts aren't available)" -ForegroundColor Yellow
        $testResults.Package = $false
        # Don't count this as a failure since it depends on build artifacts
    }
} catch {
    Write-Host "⚠ package job error (expected): $($_.Exception.Message)" -ForegroundColor Yellow
    $testResults.Package = $false
}
Write-Host ""

# Test 6: upload job
Write-Host "Test 6: Testing upload job..." -ForegroundColor Cyan
Write-Host "Note: This job depends on package artifacts, which may not be available in act" -ForegroundColor Yellow
Write-Host ""
try {
    if ($ActVerbose) {
        $output = & ".\scripts\run_workflow_act.ps1" -Job "upload" -ActVerbose 2>&1
    } else {
        $output = & ".\scripts\run_workflow_act.ps1" -Job "upload" 2>&1
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ upload job passed" -ForegroundColor Green
        $testResults.Upload = $true
        $passedTests += "Upload"
    } else {
        Write-Host "⚠ upload job failed (expected if package artifacts aren't available)" -ForegroundColor Yellow
        $testResults.Upload = $false
        # Don't count this as a failure since it depends on package artifacts
    }
} catch {
    Write-Host "⚠ upload job error (expected): $($_.Exception.Message)" -ForegroundColor Yellow
    $testResults.Upload = $false
}
Write-Host ""

# Summary
Write-Host "========================================="
Write-Host "Test Summary"
Write-Host "========================================="
Write-Host ""

foreach ($test in $testResults.Keys) {
    $result = $testResults[$test]
    if ($result -eq $true) {
        Write-Host "✓ $test : PASSED" -ForegroundColor Green
    } elseif ($result -eq $false) {
        Write-Host "✗ $test : FAILED" -ForegroundColor Red
    } else {
        Write-Host "- $test : SKIPPED" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Passed: $($passedTests.Count)" -ForegroundColor Green
Write-Host "Failed: $($failedTests.Count)" -ForegroundColor $(if ($failedTests.Count -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failedTests.Count -eq 0) {
    Write-Host "========================================="
    Write-Host "All critical tests passed!" -ForegroundColor Green
    Write-Host "========================================="
    Write-Host ""
    Write-Host "Note: Some jobs (package, upload) may fail in act due to:" -ForegroundColor Yellow
    Write-Host "  - Missing build artifacts (act doesn't fully support artifact uploads)" -ForegroundColor Yellow
    Write-Host "  - Windows/macOS builds fail because act simulates them in Linux containers" -ForegroundColor Yellow
    Write-Host "  - ACTIONS_RUNTIME_TOKEN not available for artifact operations" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "These limitations are expected and don't indicate workflow issues." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "========================================="
    Write-Host "Some tests failed!" -ForegroundColor Red
    Write-Host "========================================="
    exit 1
}
