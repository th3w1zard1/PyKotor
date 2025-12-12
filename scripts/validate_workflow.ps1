#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validate publish_pykotor.yml workflow without requiring Docker/act.

.DESCRIPTION
    This script validates the workflow structure, syntax, and logic without needing
    Docker or act. It checks:
    - Workflow YAML syntax
    - Job dependencies
    - Matrix configurations
    - Tool detection logic
    - Script availability

.PARAMETER Workflow
    Path to workflow file. Default: .github/workflows/publish_pykotor.yml
#>

[CmdletBinding()]
param(
    [string]$Workflow = ".github/workflows/publish_pykotor.yml"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================="
Write-Host "Validating Workflow: $Workflow"
Write-Host "========================================="
Write-Host ""

$errors = @()
$warnings = @()

# Test 1: Check workflow file exists
if (-not (Test-Path $Workflow)) {
    Write-Host "✗ Workflow file not found: $Workflow" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Workflow file exists" -ForegroundColor Green

# Test 2: Validate YAML syntax with gh cli
Write-Host "Validating YAML syntax with gh cli..." -ForegroundColor Cyan
try {
    $null = gh workflow view publish_pykotor.yml --yaml 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Workflow YAML syntax is valid" -ForegroundColor Green
    } else {
        $errors += "Workflow YAML syntax is invalid"
        Write-Host "✗ Workflow YAML syntax error" -ForegroundColor Red
    }
} catch {
    $errors += "Failed to validate workflow syntax: $($_.Exception.Message)"
    Write-Host "✗ Failed to validate workflow syntax" -ForegroundColor Red
}

# Test 3: Validate tool detection logic
Write-Host "Validating tool detection logic..." -ForegroundColor Cyan
try {
    $output = python scripts/test_tool_detection.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        $toolCount = ($output | Select-String -Pattern "Total tools:" | ForEach-Object { ($_ -split ':')[1].Trim() })
        Write-Host "✓ Tool detection works - found $toolCount tools" -ForegroundColor Green
    } else {
        $errors += "Tool detection script failed"
        Write-Host "✗ Tool detection script failed" -ForegroundColor Red
    }
} catch {
    $errors += "Failed to run tool detection: $($_.Exception.Message)"
    Write-Host "✗ Failed to run tool detection" -ForegroundColor Red
}

# Test 4: Check compile scripts exist for detected tools
Write-Host "Validating compile scripts..." -ForegroundColor Cyan
try {
    $tools = python scripts/test_tool_detection.py 2>&1 | Select-String -Pattern "^\s+-" | ForEach-Object {
        if ($_ -match "\(build: (\w+),") {
            $matches[1]
        }
    }
    
    $missingScripts = @()
    foreach ($tool in $tools) {
        $hasScript = (Test-Path "compile/compile_$tool.ps1") -or 
                     (Test-Path "compile/compile_$tool.sh") -or 
                     (Test-Path "compile/compile_$tool.bat") -or
                     (Test-Path "compile/compile_tool.py")
        if (-not $hasScript) {
            $missingScripts += $tool
        }
    }
    
    if ($missingScripts.Count -eq 0) {
        Write-Host "✓ All tools have compile scripts or use compile_tool.py" -ForegroundColor Green
    } else {
        $warnings += "Some tools missing explicit scripts (may use compile_tool.py): $($missingScripts -join ', ')"
        Write-Host "⚠ Some tools may use compile_tool.py: $($missingScripts -join ', ')" -ForegroundColor Yellow
    }
} catch {
    $warnings += "Could not validate compile scripts: $($_.Exception.Message)"
    Write-Host "⚠ Could not validate compile scripts" -ForegroundColor Yellow
}

# Test 5: Check required scripts exist
Write-Host "Validating required scripts..." -ForegroundColor Cyan
$requiredScripts = @(
    "install_python_venv.ps1",
    "install_powershell.sh",
    "compile/compile_tool.py"
)

$missing = @()
foreach ($script in $requiredScripts) {
    if (Test-Path $script) {
        Write-Host "  ✓ $script" -ForegroundColor Green
    } else {
        $missing += $script
        Write-Host "  ✗ $script (missing)" -ForegroundColor Red
    }
}

if ($missing.Count -eq 0) {
    Write-Host "✓ All required scripts exist" -ForegroundColor Green
} else {
    $errors += "Missing required scripts: $($missing -join ', ')"
}

# Test 6: Validate workflow structure (jobs, dependencies)
Write-Host "Validating workflow structure..." -ForegroundColor Cyan
try {
    $workflowContent = Get-Content $Workflow -Raw
    
    # Check for required jobs (use multiline matching)
    $requiredJobs = @("detect-tools", "setup", "build", "package", "upload")
    $foundJobs = @()
    foreach ($job in $requiredJobs) {
        # Use multiline regex to match job definitions
        $jobPattern = "(?m)^\s+${job}:"
        if ($workflowContent -match $jobPattern) {
            $foundJobs += $job
            Write-Host "  ✓ Job '$job' found" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Job '$job' not found" -ForegroundColor Red
            $errors += "Required job '$job' not found"
        }
    }
    
    # Check build job dependencies (multiline)
    if ($workflowContent -match "(?s)build:.*?needs:\s*\[(.*?)\]") {
        $needs = $matches[1] -split ',' | ForEach-Object { $_.Trim() }
        if ($needs -contains "setup" -and $needs -contains "detect-tools") {
            Write-Host "  ✓ Build job has correct dependencies" -ForegroundColor Green
        } else {
            $errors += "Build job missing required dependencies"
            Write-Host "  ✗ Build job missing dependencies" -ForegroundColor Red
        }
    }
    
    # Check package job dependencies (multiline)
    if ($workflowContent -match "(?s)package:.*?needs:\s*package") {
        Write-Host "  ✓ Package job depends on build" -ForegroundColor Green
    } elseif ($workflowContent -match "(?s)package:.*?needs:\s*build") {
        Write-Host "  ✓ Package job depends on build" -ForegroundColor Green
    } else {
        $warnings += "Package job may not depend on build"
    }
    
    # Check upload job dependencies (multiline)
    if ($workflowContent -match "(?s)upload:.*?needs:\s*package") {
        Write-Host "  ✓ Upload job depends on package" -ForegroundColor Green
    } else {
        $warnings += "Upload job may not depend on package"
    }
    
} catch {
    $errors += "Failed to validate workflow structure: $($_.Exception.Message)"
    Write-Host "✗ Failed to validate workflow structure" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "========================================="
Write-Host "Validation Summary"
Write-Host "========================================="
Write-Host ""

if ($errors.Count -eq 0) {
    Write-Host "✓ All critical validations passed!" -ForegroundColor Green
    if ($warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "Warnings:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  ⚠ $warning" -ForegroundColor Yellow
        }
    }
    exit 0
} else {
    Write-Host "✗ Validation failed with $($errors.Count) error(s):" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  ✗ $error" -ForegroundColor Red
    }
    if ($warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "Warnings:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  ⚠ $warning" -ForegroundColor Yellow
        }
    }
    exit 1
}

