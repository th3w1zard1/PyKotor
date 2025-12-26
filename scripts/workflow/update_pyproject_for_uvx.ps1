<#
.SYNOPSIS
    Updates pyproject.toml files in Tools/Libraries for uvx compatibility.

.DESCRIPTION
    Modifies pyproject.toml to:
    1. Replace relative readme paths with local README.md
    2. Update pykotor dependency to use git URL instead of PyPI
    3. Add proper namespace package configuration
    4. Ensure scripts are properly defined

.PARAMETER Path
    Path to the tool/library directory containing pyproject.toml.

.PARAMETER All
    Process all Tools and Libraries.

.PARAMETER DryRun
    Show changes without applying them.

.PARAMETER CreateReadme
    Create a basic README.md if one doesn't exist.

.EXAMPLE
    .\update_pyproject_for_uvx.ps1 -Path Tools/HolocronToolset
    Updates pyproject.toml in HolocronToolset for uvx compatibility.

.EXAMPLE
    .\update_pyproject_for_uvx.ps1 -All -DryRun
    Shows what changes would be made to all pyproject.toml files.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false, ParameterSetName = 'Single')]
    [string]$Path,

    [Parameter(Mandatory = $false, ParameterSetName = 'All')]
    [switch]$All,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$CreateReadme
)

$scriptDir = $PSScriptRoot
$repoRoot = Split-Path -Parent $scriptDir

function Update-PyProjectToml {
    param(
        [string]$ProjectPath,
        [switch]$DryRun,
        [switch]$CreateReadme
    )
    
    $pyprojectPath = Join-Path $ProjectPath "pyproject.toml"
    if (-not (Test-Path $pyprojectPath)) {
        Write-Host "  No pyproject.toml found in $ProjectPath" -ForegroundColor Yellow
        return
    }
    
    $projectName = Split-Path -Leaf $ProjectPath
    Write-Host "Processing: $projectName" -ForegroundColor Cyan
    
    $content = Get-Content $pyprojectPath -Raw
    $originalContent = $content
    $changes = @()
    
    # 1. Fix relative readme paths
    if ($content -match 'readme\s*=\s*\{\s*file\s*=\s*"\.\./.+?"') {
        $content = $content -replace 'readme\s*=\s*\{\s*file\s*=\s*"\.\./.+?",\s*content-type\s*=\s*"text/markdown"\s*\}', 'readme = "README.md"'
        $changes += "Fixed relative readme path"
        
        # Create README if needed
        $readmePath = Join-Path $ProjectPath "README.md"
        if (-not (Test-Path $readmePath) -and $CreateReadme) {
            $readmeContent = @"
# $projectName

Part of the [PyKotor](https://github.com/OldRepublicDevs/PyKotor) ecosystem.

## Installation

```bash
pip install $($projectName.ToLower())
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/th3w1zard1/$projectName.git
```

## Usage with uvx

```bash
uvx --from "$($projectName.ToLower()) @ git+https://github.com/th3w1zard1/$projectName.git" $($projectName.ToLower())
```

## License

LGPL-3.0-or-later
"@
            if (-not $DryRun) {
                $readmeContent | Set-Content $readmePath -Encoding UTF8
            }
            $changes += "Created README.md"
        }
    }
    
    # 2. Update pykotor dependency to git URL for libraries that need it
    # Only update if it's using PyPI version (>=X.X.X syntax)
    if ($content -match '"pykotor>=[\d.]+"') {
        # Check if this is a tool that depends on pykotor
        $parentDir = Split-Path -Leaf (Split-Path -Parent $ProjectPath)
        if ($parentDir -eq "Tools") {
            $content = $content -replace '"pykotor>=[\d.]+"', '"pykotor @ git+https://github.com/OldRepublicDevs/PyKotor-lib.git"'
            $changes += "Updated pykotor dependency to git URL"
        }
    }
    
    # 3. Update pykotorgl dependency
    if ($content -match '"pykotorgl>=[\d.]+"') {
        $content = $content -replace '"pykotorgl>=[\d.]+"', '"pykotorgl @ git+https://github.com/OldRepublicDevs/PyKotorGL.git"'
        $changes += "Updated pykotorgl dependency to git URL"
    }
    
    # 4. Update pykotorfont dependency
    if ($content -match '"pykotorfont>=[\d.]+"') {
        $content = $content -replace '"pykotorfont>=[\d.]+"', '"pykotorfont @ git+https://github.com/OldRepublicDevs/PyKotorFont.git"'
        $changes += "Updated pykotorfont dependency to git URL"
    }
    
    # 5. Add namespace package config for pykotor.* packages
    if ($content -match 'pykotor\.' -and $content -notmatch 'namespaces\s*=\s*true') {
        if ($content -match '\[tool\.setuptools\.packages\.find\]') {
            $content = $content -replace '(\[tool\.setuptools\.packages\.find\][^\[]*)', "`$1namespaces = true`n"
            $changes += "Added namespace package configuration"
        }
    }
    
    # Report changes
    if ($changes.Count -gt 0) {
        Write-Host "  Changes:" -ForegroundColor Yellow
        $changes | ForEach-Object { Write-Host "    - $_" -ForegroundColor White }
        
        if (-not $DryRun) {
            $content | Set-Content $pyprojectPath -Encoding UTF8 -NoNewline
            Write-Host "  Updated pyproject.toml" -ForegroundColor Green
        } else {
            Write-Host "  [DRY RUN] Would update pyproject.toml" -ForegroundColor Magenta
        }
    } else {
        Write-Host "  No changes needed" -ForegroundColor Gray
    }
    
    return $changes.Count -gt 0
}

# Main logic
if ($All) {
    $paths = @()
    
    # Collect all Tools
    $toolsDir = Join-Path $repoRoot "Tools"
    if (Test-Path $toolsDir) {
        Get-ChildItem $toolsDir -Directory | ForEach-Object {
            $paths += $_.FullName
        }
    }
    
    # Collect all Libraries (except Utility which is part of PyKotor)
    $libsDir = Join-Path $repoRoot "Libraries"
    if (Test-Path $libsDir) {
        Get-ChildItem $libsDir -Directory | Where-Object { $_.Name -ne "Utility" } | ForEach-Object {
            $paths += $_.FullName
        }
    }
    
    Write-Host "Processing $($paths.Count) projects..." -ForegroundColor Cyan
    Write-Host ""
    
    $updated = 0
    foreach ($p in $paths) {
        if (Update-PyProjectToml -ProjectPath $p -DryRun:$DryRun -CreateReadme:$CreateReadme) {
            $updated++
        }
        Write-Host ""
    }
    
    Write-Host "=" * 50 -ForegroundColor Green
    Write-Host "Updated $updated / $($paths.Count) projects" -ForegroundColor Green
}
elseif ($Path) {
    $fullPath = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $repoRoot $Path }
    if (-not (Test-Path $fullPath)) {
        Write-Error "Path not found: $fullPath"
        exit 1
    }
    Update-PyProjectToml -ProjectPath $fullPath -DryRun:$DryRun -CreateReadme:$CreateReadme
}
else {
    Write-Error "Specify either -Path or -All"
    exit 1
}

