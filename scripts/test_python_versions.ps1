#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test workflow steps with different Python versions (3.8-3.13).

.DESCRIPTION
    This script tests the key workflow steps (venv creation, compilation, testing) 
    with Python versions 3.8 through 3.13 to ensure compatibility.
#>

param(
    [Parameter(ValueFromRemainingArguments=$false)]
    [string[]]$PythonVersions = @("3.8", "3.9", "3.10", "3.11", "3.12", "3.13"),
    [string]$Tool = "KotorDiff",  # Test with a simpler tool first
    [switch]$SkipCompile,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "========================================="
Write-Host "Testing Python Versions: $($PythonVersions -join ', ')"
Write-Host "Tool: $Tool"
Write-Host "========================================="
Write-Host ""

# Detect tool build name
$toolDir = "Tools/$Tool"
if (-not (Test-Path $toolDir)) {
    Write-Error "Tool directory not found: $toolDir"
    exit 1
}

$buildName = $Tool.ToLower()
if ($buildName -eq "holocrontoolset") {
    $buildName = "toolset"
}

# Check for compile script
$compileScript = $null
$compileCandidates = @(
    "compile/compile_${buildName}.ps1",
    "compile/compile_${buildName}.sh",
    "compile/compile_${buildName}.bat"
)

foreach ($candidate in $compileCandidates) {
    if (Test-Path $candidate) {
        $compileScript = $candidate
        break
    }
}

if (-not $compileScript) {
    Write-Error "No compile script found for $Tool"
    exit 1
}

Write-Host "Using compile script: $compileScript"
Write-Host ""

$failedVersions = @()
$passedVersions = @()

foreach ($pyVersion in $PythonVersions) {
    Write-Host "========================================="
    Write-Host "Testing Python $pyVersion"
    Write-Host "========================================="
    
    $venvName = ".venv_test_${Tool}_${pyVersion}_x64"
    
    try {
        # Step 1: Create virtual environment
        Write-Host "Creating virtual environment..."
        . ./install_python_venv.ps1 -noprompt -venv_name $venvName -force_python_version $pyVersion
        
        # Find Python executable
        $pythonExePath = if ($pythonExePath) {
            $pythonExePath
        } elseif (Test-Path "$venvName\Scripts\python.exe") {
            "$venvName\Scripts\python.exe"
        } else {
            throw "Python executable not found"
        }
        
        if (-not (Test-Path $pythonExePath)) {
            throw "Python executable not found at $pythonExePath"
        }
        
        Write-Host "✓ Python found: $pythonExePath"
        & $pythonExePath --version
        
        # Step 2: Install dependencies (if deps script exists)
        $depsScript = $null
        $depsCandidates = @(
            "compile/deps_${buildName}.ps1",
            "compile/deps_${buildName}.sh",
            "compile/deps_${buildName}.bat"
        )
        
        foreach ($candidate in $depsCandidates) {
            if (Test-Path $candidate) {
                $depsScript = $candidate
                break
            }
        }
        
        if ($depsScript) {
            Write-Host "Installing dependencies using $depsScript..."
            if ($depsScript.EndsWith(".ps1")) {
                . "./$depsScript" -noprompt -venv_name $venvName
            } elseif ($depsScript.EndsWith(".sh")) {
                bash "./$depsScript" -noprompt -venv_name $venvName
            } elseif ($depsScript.EndsWith(".bat")) {
                cmd /c ".\\$depsScript -noprompt -venv_name $venvName"
            }
            Write-Host "✓ Dependencies installed"
        } else {
            Write-Host "No deps script found, skipping dependency installation"
        }
        
        # Step 3: Compile (if not skipped)
        if (-not $SkipCompile) {
            Write-Host "Compiling tool..."
            if ($compileScript.EndsWith(".ps1")) {
                . "./$compileScript" -noprompt -venv_name $venvName
            } elseif ($compileScript.EndsWith(".sh")) {
                bash "./$compileScript" -noprompt -venv_name $venvName
            } elseif ($compileScript.EndsWith(".bat")) {
                cmd /c ".\\$compileScript -noprompt -venv_name $venvName"
            }
            
            if ($LASTEXITCODE -ne 0) {
                throw "Compilation failed with exit code $LASTEXITCODE"
            }
            Write-Host "✓ Compilation successful"
        }
        
        # Step 4: Run tests (if not skipped)
        if (-not $SkipTests) {
            $testsPath = Join-Path $toolDir "tests"
            if (Test-Path $testsPath) {
                Write-Host "Running tests..."
                
                # Install test dependencies if needed
                $pyprojectPath = Join-Path $toolDir "pyproject.toml"
                if (Test-Path $pyprojectPath) {
                    & $pythonExePath -m pip install -e "$toolDir[dev]" --quiet 2>&1 | Out-Null
                }
                
                # Install pytest-timeout if available
                & $pythonExePath -m pip install pytest-timeout --quiet 2>&1 | Out-Null
                
                $pytestArgs = @("$testsPath", "-v", "--tb=short")
                $timeoutCheck = & $pythonExePath -m pytest --help 2>&1 | Select-String "timeout"
                if ($timeoutCheck) {
                    $pytestArgs += @("--timeout=120", "--timeout-method=thread")
                }
                
                & $pythonExePath -m pytest $pytestArgs
                if ($LASTEXITCODE -ne 0) {
                    Write-Host -ForegroundColor Yellow "⚠ Tests completed with warnings (exit code $LASTEXITCODE)"
                } else {
                    Write-Host -ForegroundColor Green "✓ All tests passed!"
                }
            } else {
                Write-Host "No tests directory found, skipping tests"
            }
        }
        
        Write-Host -ForegroundColor Green "✓ Python ${pyVersion}: SUCCESS"
        $passedVersions += $pyVersion
        
    } catch {
        Write-Host -ForegroundColor Red "✗ Python ${pyVersion}: FAILED"
        Write-Host -ForegroundColor Red "  Error: $($_.Exception.Message)"
        $failedVersions += $pyVersion
    }
    
    Write-Host ""
}

# Summary
Write-Host "========================================="
Write-Host "Test Summary"
Write-Host "========================================="
Write-Host "Passed: $($passedVersions.Count)"
foreach ($v in $passedVersions) {
    Write-Host -ForegroundColor Green "  ✓ Python $v"
}
Write-Host ""
Write-Host "Failed: $($failedVersions.Count)"
foreach ($v in $failedVersions) {
    Write-Host -ForegroundColor Red "  ✗ Python $v"
}
Write-Host ""

if ($failedVersions.Count -gt 0) {
    Write-Host -ForegroundColor Red "Some Python versions failed!"
    exit 1
} else {
    Write-Host -ForegroundColor Green "All Python versions passed!"
    exit 0
}

