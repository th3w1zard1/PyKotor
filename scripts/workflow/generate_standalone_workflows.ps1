<#
.SYNOPSIS
    Generates GitHub Actions workflows for standalone Tool/Library repositories.

.DESCRIPTION
    Creates standard CI/CD workflow files for Tools and Libraries that can be used
    when they're published as independent GitHub repositories.

.PARAMETER Path
    Path to the tool/library directory.

.PARAMETER All
    Generate workflows for all Tools and Libraries.

.PARAMETER DryRun
    Show what would be generated without creating files.

.EXAMPLE
    .\generate_standalone_workflows.ps1 -Path Tools/HolocronToolset
    Generates workflows for HolocronToolset.

.EXAMPLE
    .\generate_standalone_workflows.ps1 -All
    Generates workflows for all Tools and Libraries.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false, ParameterSetName = 'Single')]
    [string]$Path,

    [Parameter(Mandatory = $false, ParameterSetName = 'All')]
    [switch]$All,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

$scriptDir = $PSScriptRoot
$repoRoot = Split-Path -Parent $scriptDir

# Determine if this is a library (contributes to pykotor namespace)
function Get-IsNamespaceLibrary {
    param([string]$ProjectPath)
    
    $name = Split-Path -Leaf $ProjectPath
    return $name -in @("PyKotor", "PyKotorGL", "PyKotorFont")
}

# Determine if this needs PyQt/GUI testing
function Get-NeedsQtTesting {
    param([string]$ProjectPath)
    
    $pyprojectPath = Join-Path $ProjectPath "pyproject.toml"
    if (Test-Path $pyprojectPath) {
        $content = Get-Content $pyprojectPath -Raw
        return $content -match "PyQt5|PySide6|qtpy"
    }
    return $false
}

# Get the package name from pyproject.toml
function Get-PackageName {
    param([string]$ProjectPath)
    
    $pyprojectPath = Join-Path $ProjectPath "pyproject.toml"
    if (Test-Path $pyprojectPath) {
        $content = Get-Content $pyprojectPath -Raw
        if ($content -match 'name\s*=\s*"([^"]+)"') {
            return $matches[1]
        }
    }
    return (Split-Path -Leaf $ProjectPath).ToLower()
}

# Get dependencies from pyproject.toml
function Get-PykotorDependencies {
    param([string]$ProjectPath)
    
    $deps = @()
    $pyprojectPath = Join-Path $ProjectPath "pyproject.toml"
    if (Test-Path $pyprojectPath) {
        $content = Get-Content $pyprojectPath -Raw
        if ($content -match '"pykotor[^"]*"') { $deps += "pykotor" }
        if ($content -match '"pykotorgl[^"]*"') { $deps += "pykotorgl" }
    }
    return $deps
}

function Generate-CiWorkflow {
    param(
        [string]$ProjectPath,
        [string]$PackageName,
        [bool]$IsNamespaceLib,
        [bool]$NeedsQt,
        [string[]]$PyKotorDeps
    )
    
    $projectName = Split-Path -Leaf $ProjectPath
    
    # Determine install commands based on dependencies
    $installCommands = @()
    if ($PyKotorDeps -contains "pykotor") {
        $installCommands += 'pip install "pykotor @ git+https://github.com/OldRepublicDevs/PyKotor-lib.git"'
    }
    if ($PyKotorDeps -contains "pykotorgl") {
        $installCommands += 'pip install "pykotorgl @ git+https://github.com/OldRepublicDevs/PyKotorGL.git"'
    }
    $installCommands += "pip install -e .[dev]"
    
    $installSection = ($installCommands | ForEach-Object { "          $_" }) -join "`n"
    
    # For namespace libraries, just install self
    if ($IsNamespaceLib) {
        $installSection = "          pip install -e .[dev]"
    }
    
    # Qt-specific test setup
    $qtSetup = ""
    if ($NeedsQt) {
        $qtSetup = @"

      - name: Install Qt dependencies (Linux)
        if: runner.os == 'Linux'
        run: |
          sudo apt-get update
          sudo apt-get install -y xvfb libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0
"@
    }
    
    $testCommand = if ($NeedsQt -and $ProjectPath -notmatch "Libraries") {
        "xvfb-run -a pytest tests/ -v --tb=short --maxfail=5 || pytest tests/ -v --tb=short --maxfail=5"
    } else {
        "pytest tests/ -v --tb=short --maxfail=5"
    }
    
    return @"
name: CI

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]
  workflow_dispatch:

jobs:
  test:
    name: Test Python `${{ matrix.python-version }} on `${{ matrix.os }}
    runs-on: `${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]
        exclude:
          - os: macos-latest
            python-version: "3.9"
          - os: windows-latest
            python-version: "3.9"

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python `${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: `${{ matrix.python-version }}
          cache: 'pip'
$qtSetup
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip setuptools wheel
$installSection

      - name: Verify import
        run: |
          python -c "import $PackageName; print('$projectName imported successfully')"

      - name: Run tests
        run: |
          $testCommand
        continue-on-error: true

  build:
    name: Build package
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip setuptools wheel build

      - name: Build package
        run: |
          python -m build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/*
          retention-days: 30
"@
}

function Generate-LintWorkflow {
    param(
        [string]$ProjectPath,
        [string]$PackageName
    )
    
    return @"
name: Lint

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]
  workflow_dispatch:

jobs:
  ruff:
    name: Ruff Linting
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install ruff
        run: |
          pip install ruff

      - name: Run ruff check
        run: |
          ruff check . --output-format=github

      - name: Check formatting
        run: |
          ruff format --check .
"@
}

function Generate-ReleaseWorkflow {
    param(
        [string]$ProjectPath,
        [string]$PackageName
    )
    
    $projectName = Split-Path -Leaf $ProjectPath
    
    return @"
name: Release

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  publish:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/project/$PackageName/
    permissions:
      id-token: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip setuptools wheel build twine

      - name: Build package
        run: |
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          skip-existing: true
"@
}

function Process-Project {
    param(
        [string]$ProjectPath,
        [switch]$DryRun
    )
    
    $projectName = Split-Path -Leaf $ProjectPath
    
    # Verify pyproject.toml exists
    $pyprojectPath = Join-Path $ProjectPath "pyproject.toml"
    if (-not (Test-Path $pyprojectPath)) {
        Write-Host "Skipping: $projectName (no pyproject.toml)" -ForegroundColor DarkGray
        return
    }
    
    Write-Host "Processing: $projectName" -ForegroundColor Cyan
    
    $isNamespaceLib = Get-IsNamespaceLibrary $ProjectPath
    $needsQt = Get-NeedsQtTesting $ProjectPath
    $packageName = Get-PackageName $ProjectPath
    $pykotorDeps = Get-PykotorDependencies $ProjectPath
    
    Write-Host "  Package name: $packageName" -ForegroundColor Gray
    Write-Host "  Is namespace lib: $isNamespaceLib" -ForegroundColor Gray
    Write-Host "  Needs Qt: $needsQt" -ForegroundColor Gray
    Write-Host "  PyKotor deps: $($pykotorDeps -join ', ')" -ForegroundColor Gray
    
    $workflowDir = Join-Path $ProjectPath ".github" "workflows"
    
    if (-not $DryRun) {
        if (-not (Test-Path $workflowDir)) {
            New-Item -ItemType Directory -Path $workflowDir -Force | Out-Null
        }
    }
    
    # Generate CI workflow
    $ciWorkflow = Generate-CiWorkflow -ProjectPath $ProjectPath -PackageName $packageName -IsNamespaceLib $isNamespaceLib -NeedsQt $needsQt -PyKotorDeps $pykotorDeps
    $ciPath = Join-Path $workflowDir "ci.yml"
    if (-not $DryRun) {
        $ciWorkflow | Set-Content $ciPath -Encoding UTF8
        Write-Host "  Created: .github/workflows/ci.yml" -ForegroundColor Green
    } else {
        Write-Host "  Would create: .github/workflows/ci.yml" -ForegroundColor Magenta
    }
    
    # Generate lint workflow
    $lintWorkflow = Generate-LintWorkflow -ProjectPath $ProjectPath -PackageName $packageName
    $lintPath = Join-Path $workflowDir "lint.yml"
    if (-not $DryRun) {
        $lintWorkflow | Set-Content $lintPath -Encoding UTF8
        Write-Host "  Created: .github/workflows/lint.yml" -ForegroundColor Green
    } else {
        Write-Host "  Would create: .github/workflows/lint.yml" -ForegroundColor Magenta
    }
    
    # Generate release workflow
    $releaseWorkflow = Generate-ReleaseWorkflow -ProjectPath $ProjectPath -PackageName $packageName
    $releasePath = Join-Path $workflowDir "release.yml"
    if (-not $DryRun) {
        $releaseWorkflow | Set-Content $releasePath -Encoding UTF8
        Write-Host "  Created: .github/workflows/release.yml" -ForegroundColor Green
    } else {
        Write-Host "  Would create: .github/workflows/release.yml" -ForegroundColor Magenta
    }
}

# Main logic
if ($All) {
    $paths = @()
    
    # Collect all Tools (must have pyproject.toml)
    $toolsDir = Join-Path $repoRoot "Tools"
    if (Test-Path $toolsDir) {
        Get-ChildItem $toolsDir -Directory | ForEach-Object {
            if (Test-Path (Join-Path $_.FullName "pyproject.toml")) {
                $paths += $_.FullName
            }
        }
    }
    
    # Collect all Libraries (except Utility, must have pyproject.toml)
    $libsDir = Join-Path $repoRoot "Libraries"
    if (Test-Path $libsDir) {
        Get-ChildItem $libsDir -Directory | Where-Object { $_.Name -ne "Utility" } | ForEach-Object {
            if (Test-Path (Join-Path $_.FullName "pyproject.toml")) {
                $paths += $_.FullName
            }
        }
    }
    
    Write-Host "Generating workflows for $($paths.Count) projects..." -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($p in $paths) {
        Process-Project -ProjectPath $p -DryRun:$DryRun
        Write-Host ""
    }
}
elseif ($Path) {
    $fullPath = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $repoRoot $Path }
    if (-not (Test-Path $fullPath)) {
        Write-Error "Path not found: $fullPath"
        exit 1
    }
    Process-Project -ProjectPath $fullPath -DryRun:$DryRun
}
else {
    Write-Error "Specify either -Path or -All"
    exit 1
}

Write-Host ""
Write-Host "Done! Don't forget to commit and push the workflow files." -ForegroundColor Green

