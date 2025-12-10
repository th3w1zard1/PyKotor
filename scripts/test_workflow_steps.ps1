#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test individual workflow steps to identify issues before running with act or gh cli.

.DESCRIPTION
    This script tests the key workflow steps manually to identify and fix issues.
#>

$ErrorActionPreference = "Stop"

Write-Host "========================================="
Write-Host "Testing Workflow Steps"
Write-Host "========================================="
Write-Host ""

# Step 1: Test tool detection (detect-tools job)
Write-Host "Step 1: Testing tool detection..."
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

with open("tools_matrix.json", "w") as fh:
    json.dump(tools, fh, indent=2)
"@

$detectScript | python - | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tool detection failed"
    exit 1
}

$toolsJson = Get-Content "tools_matrix.json" | ConvertFrom-Json
Write-Host "✓ Tool detection successful: $($toolsJson.Count) tools found"
Write-Host ""

# Step 2: Test setup job (environment variables)
Write-Host "Step 2: Testing setup job (environment variables)..."
$osRunners = @("windows-latest", "ubuntu-latest", "macos-latest")
$pythonVersions = @("3.8", "3.9", "3.10", "3.11", "3.12", "3.13")
$architectures = @("x86", "x64")

Write-Host "OS Runners: $($osRunners -join ', ')"
Write-Host "Python Versions: $($pythonVersions -join ', ')"
Write-Host "Architectures: $($architectures -join ', ')"
Write-Host "✓ Setup job simulation successful"
Write-Host ""

# Step 3: Test install_powershell.sh (if on Linux/macOS, skip on Windows)
Write-Host "Step 3: Testing install_powershell.sh..."
if ($IsLinux -or $IsMacOS) {
    if (Test-Path "install_powershell.sh") {
        Write-Host "Testing install_powershell.sh..."
        bash ./install_powershell.sh
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ install_powershell.sh works"
        } else {
            Write-Host "⚠ install_powershell.sh may have issues (exit code: $LASTEXITCODE)"
        }
    } else {
        Write-Host "⚠ install_powershell.sh not found"
    }
} else {
    Write-Host "Skipping (Windows - PowerShell already available)"
}
Write-Host ""

# Step 4: Test install_python_venv.ps1 with a test version
Write-Host "Step 4: Testing install_python_venv.ps1..."
$testVenvName = ".venv_test_workflow"
try {
    Write-Host "Testing with Python 3.13..."
    . ./install_python_venv.ps1 -noprompt -venv_name $testVenvName -force_python_version "3.13"
    
    if ($pythonExePath -and (Test-Path $pythonExePath)) {
        Write-Host "✓ install_python_venv.ps1 works (Python: $pythonExePath)"
        & $pythonExePath --version
    } elseif (Test-Path "$testVenvName\Scripts\python.exe") {
        Write-Host "✓ install_python_venv.ps1 works (Python found in venv)"
        & "$testVenvName\Scripts\python.exe" --version
    } else {
        Write-Host "⚠ install_python_venv.ps1 may have issues (Python not found)"
    }
} catch {
    Write-Host "⚠ install_python_venv.ps1 error: $($_.Exception.Message)"
}
Write-Host ""

# Step 5: Test compile script detection
Write-Host "Step 5: Testing compile script detection..."
foreach ($tool in $toolsJson) {
    $buildName = $tool.build_name
    $compileCandidates = @(
        "compile/compile_${buildName}.ps1",
        "compile/compile_${buildName}.sh",
        "compile/compile_${buildName}.bat"
    )
    
    $found = $false
    foreach ($candidate in $compileCandidates) {
        if (Test-Path $candidate) {
            Write-Host "  ✓ $($tool.display_name): Found $candidate"
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-Host "  ✗ $($tool.display_name): No compile script found"
    }
}
Write-Host ""

Write-Host "========================================="
Write-Host "Workflow Step Testing Complete"
Write-Host "========================================="

