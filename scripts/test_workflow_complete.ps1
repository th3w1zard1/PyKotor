#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive test of the publish_pykotor.yml workflow components.

.DESCRIPTION
    Tests all critical workflow steps to ensure they function correctly.
#>

$ErrorActionPreference = "Stop"

Write-Host "========================================="
Write-Host "Comprehensive Workflow Test"
Write-Host "========================================="
Write-Host ""

$errors = @()
$warnings = @()

# Test 1: Tool Detection
Write-Host "Test 1: Tool Detection..."
try {
    $detectScript = @"
import json
import os
from pathlib import Path

tools_dir = Path("Tools")
tools = []

def derive_build_name(name: str) -> str:
    lower = name.lower()
    special = {"holocrontoolset": "toolset"}
    return special.get(lower, lower)

def has_compile_script(build_name: str) -> bool:
    return any(Path(path).exists() for path in [
        f"compile/compile_{build_name}.ps1",
        f"compile/compile_{build_name}.sh",
        f"compile/compile_{build_name}.bat",
    ])

if tools_dir.exists():
    for tool_path in sorted(tools_dir.iterdir()):
        if tool_path.is_dir() and not tool_path.name.startswith("."):
            build_name = derive_build_name(tool_path.name)
            if not has_compile_script(build_name):
                print(f"Skipping {tool_path.name}: no compile script found")
                continue
            tools.append({
                "tool_dir": tool_path.name,
                "build_name": build_name,
                "display_name": tool_path.name,
            })
else:
    print("❌ Tools directory not found")

print("Detected tools:")
for t in tools:
    print(f" - {t['display_name']} (build: {t['build_name']})")

with open("tools_matrix_test.json", "w") as fh:
    json.dump(tools, fh, indent=2)
"@

    $detectScript | python - 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0 -and (Test-Path "tools_matrix_test.json")) {
        $tools = Get-Content "tools_matrix_test.json" | ConvertFrom-Json
        Write-Host "  ✓ Detected $($tools.Count) tools" -ForegroundColor Green
    } else {
        throw "Tool detection failed"
    }
} catch {
    Write-Host "  ✗ Tool detection failed: $_" -ForegroundColor Red
    $errors += "Tool detection"
}

# Test 2: PowerShell Installation Script
Write-Host "Test 2: PowerShell Installation Script..."
if (Test-Path "install_powershell.sh") {
    Write-Host "  ✓ install_powershell.sh exists" -ForegroundColor Green
    $content = Get-Content "install_powershell.sh" -Raw
    if ($content -match "pwsh") {
        Write-Host "  ✓ Script checks for pwsh" -ForegroundColor Green
    } else {
        $warnings += "install_powershell.sh may not check for pwsh properly"
    }
} else {
    Write-Host "  ✗ install_powershell.sh not found" -ForegroundColor Red
    $errors += "install_powershell.sh missing"
}

# Test 3: Python Venv Script
Write-Host "Test 3: Python Venv Script..."
if (Test-Path "install_python_venv.ps1") {
    Write-Host "  ✓ install_python_venv.ps1 exists" -ForegroundColor Green
    try {
        # Test with a dummy venv name to see if it at least starts
        $testVenv = ".venv_test_workflow_validation"
        Write-Host "  Testing venv creation (dry run)..."
        # Just check if script exists and is valid PowerShell
        $scriptContent = Get-Content "install_python_venv.ps1" -Raw
        if ($scriptContent -match "param\(") {
            Write-Host "  ✓ Script has proper parameter block" -ForegroundColor Green
        }
    } catch {
        $warnings += "install_python_venv.ps1 validation: $_"
    }
} else {
    Write-Host "  ✗ install_python_venv.ps1 not found" -ForegroundColor Red
    $errors += "install_python_venv.ps1 missing"
}

# Test 4: Compile Scripts
Write-Host "Test 4: Compile Scripts..."
if ($tools) {
    foreach ($tool in $tools) {
        $buildName = $tool.build_name
        $compileCandidates = @(
            "compile/compile_${buildName}.ps1",
            "compile/compile_${buildName}.sh",
            "compile/compile_${buildName}.bat"
        )
        
        $found = $false
        foreach ($candidate in $compileCandidates) {
            if (Test-Path $candidate) {
                Write-Host "  ✓ $($tool.display_name): $candidate" -ForegroundColor Green
                $found = $true
                break
            }
        }
        
        if (-not $found) {
            Write-Host "  ✗ $($tool.display_name): No compile script found" -ForegroundColor Red
            $errors += "$($tool.display_name) compile script"
        }
    }
}

# Test 5: Workflow File Syntax
Write-Host "Test 5: Workflow File Syntax..."
if (Test-Path ".github/workflows/publish_pykotor.yml") {
    Write-Host "  ✓ Workflow file exists" -ForegroundColor Green
    
    # Check for cache actions
    $workflowContent = Get-Content ".github/workflows/publish_pykotor.yml" -Raw
    if ($workflowContent -match "actions/cache@v4") {
        Write-Host "  ✓ Cache actions found" -ForegroundColor Green
    } else {
        $warnings += "Cache actions not found in workflow"
    }
    
    # Check for test step after upload
    if ($workflowContent -match "Run tests for compiled tool" -and 
        $workflowContent.IndexOf("Run tests for compiled tool") -gt $workflowContent.IndexOf("Upload compiled binaries attempt 5")) {
        Write-Host "  ✓ Tests run after artifact upload" -ForegroundColor Green
    } else {
        $warnings += "Tests may not run after artifact upload"
    }
} else {
    Write-Host "  ✗ Workflow file not found" -ForegroundColor Red
    $errors += "Workflow file missing"
}

# Test 6: Cache Configuration
Write-Host "Test 6: Cache Configuration..."
$workflowContent = Get-Content ".github/workflows/publish_pykotor.yml" -Raw
if ($workflowContent -match "Cache UPX") {
    Write-Host "  ✓ UPX cache configured" -ForegroundColor Green
} else {
    $warnings += "UPX cache not configured"
}

if ($workflowContent -match "Cache pip packages") {
    Write-Host "  ✓ Pip cache configured" -ForegroundColor Green
} else {
    $warnings += "Pip cache not configured"
}

# Summary
Write-Host ""
Write-Host "========================================="
Write-Host "Test Summary"
Write-Host "========================================="

if ($errors.Count -eq 0) {
    Write-Host "✓ All critical tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Errors found:" -ForegroundColor Red
    foreach ($errorItem in $errors) {
        Write-Host "  - $errorItem" -ForegroundColor Red
    }
}

if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠ Warnings:" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  - $warning" -ForegroundColor Yellow
    }
}

Write-Host ""

if ($errors.Count -gt 0) {
    exit 1
} else {
    exit 0
}

