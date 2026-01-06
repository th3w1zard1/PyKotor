<#
.SYNOPSIS
    Removes a submodule and converts it back to a regular tracked directory (inverse of create_submodule_repo.ps1).

.DESCRIPTION
    This script reverses the submodule-ification process by:
    1. Removing the submodule entry from .gitmodules
    2. Removing the submodule entry from .git/config
    3. Removing the submodule's cached git directory from .git/modules/
    4. Converting the submodule directory to a regular tracked directory
    5. Optionally deleting the remote GitHub repository

.PARAMETER Tool
    The name of the tool (folder name in Tools/) to un-submodule.
    Mutually exclusive with -Library.

.PARAMETER Library
    The name of the library (folder name in Libraries/) to un-submodule.
    Mutually exclusive with -Tool.

.PARAMETER DeleteRemoteRepo
    If specified, also deletes the remote GitHub repository.
    USE WITH CAUTION - this is destructive and irreversible!

.PARAMETER GitHubUser
    The GitHub username/organization. Defaults to 'th3w1zard1'.

.PARAMETER DryRun
    If specified, shows what would be done without making any changes.

.PARAMETER Force
    If specified, skips confirmation prompts.

.EXAMPLE
    .\remove_submodule_repo.ps1 -Tool HolocronToolset
    Converts Tools/HolocronToolset from a submodule to a regular directory.

.EXAMPLE
    .\remove_submodule_repo.ps1 -Library PyKotorGL -DeleteRemoteRepo
    Removes the submodule AND deletes the remote GitHub repository.

.EXAMPLE
    .\remove_submodule_repo.ps1 -Tool KotorCLI -DryRun
    Shows what would be done without making changes.

.NOTES
    Requires: Git to be installed.
    If -DeleteRemoteRepo is used, requires GitHub CLI (gh) to be installed and authenticated.
    Run from the PyKotor repository root directory.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false, ParameterSetName = 'Tool')]
    [string]$Tool,

    [Parameter(Mandatory = $false, ParameterSetName = 'Library')]
    [string]$Library,

    [Parameter(Mandatory = $false)]
    [switch]$DeleteRemoteRepo,

    [Parameter(Mandatory = $false)]
    [string]$GitHubUser = "th3w1zard1",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

# Ensure exactly one of Tool or Library is provided
if (-not $Tool -and -not $Library) {
    Write-Error "You must specify either -Tool or -Library parameter."
    Write-Host ""
    Write-Host "Usage examples:"
    Write-Host "  .\remove_submodule_repo.ps1 -Tool HolocronToolset"
    Write-Host "  .\remove_submodule_repo.ps1 -Library PyKotorGL"
    Write-Host "  .\remove_submodule_repo.ps1 -Tool KotorCLI -DryRun"
    Write-Host "  .\remove_submodule_repo.ps1 -Tool KotorMCP -DeleteRemoteRepo"
    exit 1
}

if ($Tool -and $Library) {
    Write-Error "Cannot specify both -Tool and -Library. Choose one."
    exit 1
}

# Find repository root
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
    $repoRoot = Get-Location
    if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
        Write-Error "Cannot find PyKotor repository root. Run this script from the repo root or scripts folder."
        exit 1
    }
}

if ($Tool) {
    $category = "Tools"
    $name = $Tool
    $localPath = Join-Path $repoRoot "Tools" $Tool
} else {
    $category = "Libraries"
    $name = $Library
    $localPath = Join-Path $repoRoot "Libraries" $Library
}

$submodulePath = "$category/$name"
$repoName = $name  # Default repo name matches folder name

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "PyKotor Submodule Remover (Inverse Operation)" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Category:       $category"
Write-Host "  Name:           $name"
Write-Host "  Local Path:     $localPath"
Write-Host "  Submodule Path: $submodulePath"
if ($DeleteRemoteRepo) {
    Write-Host "  GitHub User:    $GitHubUser"
    Write-Host "  DELETE REMOTE:  YES (DESTRUCTIVE!)" -ForegroundColor Red
}
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN MODE - No changes will be made]" -ForegroundColor Magenta
    Write-Host ""
}

# Validate the local path exists
if (-not (Test-Path $localPath)) {
    Write-Error "Directory not found: $localPath"
    exit 1
}

# Check if it's actually a submodule
$gitmodulesPath = Join-Path $repoRoot ".gitmodules"
$isSubmodule = $false
$submoduleUrl = ""

if (Test-Path $gitmodulesPath) {
    $gitmodulesContent = Get-Content $gitmodulesPath -Raw
    if ($gitmodulesContent -match [regex]::Escape("path = $submodulePath")) {
        $isSubmodule = $true
        # Extract the URL from .gitmodules
        if ($gitmodulesContent -match "\[submodule `"$([regex]::Escape($submodulePath))`"\][^\[]*url\s*=\s*([^\r\n]+)") {
            $submoduleUrl = $matches[1].Trim()
            Write-Host "  Submodule URL:  $submoduleUrl" -ForegroundColor Yellow
            # Try to extract repo name from URL
            if ($submoduleUrl -match "/([^/]+)\.git$") {
                $repoName = $matches[1]
            }
        }
    }
}

# Check for .git file (gitdir reference) or .git directory
$gitPath = Join-Path $localPath ".git"
$hasGitDir = Test-Path $gitPath
$isGitFile = $hasGitDir -and (Test-Path $gitPath -PathType Leaf)
$isGitFolder = $hasGitDir -and (Test-Path $gitPath -PathType Container)

Write-Host "Detection:" -ForegroundColor Yellow
Write-Host "  Is in .gitmodules:  $isSubmodule"
Write-Host "  Has .git:           $hasGitDir"
if ($hasGitDir) {
    Write-Host "  .git type:          $(if ($isGitFile) { 'File (gitdir reference)' } else { 'Directory (standalone)' })"
}
Write-Host ""

if (-not $isSubmodule -and -not $hasGitDir) {
    Write-Host "This directory is already a regular tracked directory (not a submodule)." -ForegroundColor Green
    exit 0
}

# Confirm action
if (-not $Force -and -not $DryRun) {
    Write-Host "This will:" -ForegroundColor Yellow
    Write-Host "  1. Remove submodule entry from .gitmodules" -ForegroundColor White
    Write-Host "  2. Remove submodule entry from .git/config" -ForegroundColor White
    Write-Host "  3. Remove cached submodule data from .git/modules/" -ForegroundColor White
    Write-Host "  4. Remove .git from the submodule directory" -ForegroundColor White
    Write-Host "  5. Add all files as regular tracked files" -ForegroundColor White
    if ($DeleteRemoteRepo) {
        Write-Host "  6. DELETE the remote GitHub repository $GitHubUser/$repoName" -ForegroundColor Red
    }
    Write-Host ""
    $confirm = Read-Host "Proceed? (y/N)"
    if ($confirm -notmatch "^[Yy]") {
        Write-Host "Aborted by user." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "Executing steps..." -ForegroundColor Cyan
Write-Host ""

function Invoke-Step {
    param(
        [string]$Description,
        [scriptblock]$Action,
        [switch]$Critical,
        [switch]$IgnoreError
    )
    
    Write-Host "→ $Description" -ForegroundColor Green
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would execute action" -ForegroundColor DarkGray
        return $true
    }
    
    try {
        & $Action
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0 -and -not $IgnoreError) {
            throw "Command failed with exit code $LASTEXITCODE"
        }
        return $true
    }
    catch {
        Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
        if ($Critical) {
            exit 1
        }
        return $false
    }
}

# Step 1: Deinit the submodule (removes from .git/config)
if ($isSubmodule) {
    Invoke-Step "Deinitializing submodule" {
        Push-Location $repoRoot
        git submodule deinit -f $submodulePath 2>&1
        Pop-Location
    } -IgnoreError
}

# Step 2: Remove from git index (keeps files)
Invoke-Step "Removing submodule from git index" {
    Push-Location $repoRoot
    git rm -rf --cached $submodulePath 2>&1
    Pop-Location
} -IgnoreError

# Step 3: Remove from .git/modules/
$modulesPath = Join-Path $repoRoot ".git" "modules" $submodulePath
if (Test-Path $modulesPath) {
    Invoke-Step "Removing cached submodule data from .git/modules/" {
        Remove-Item -Recurse -Force $modulesPath
    }
} else {
    Write-Host "→ No cached submodule data found in .git/modules/" -ForegroundColor DarkGray
}

# Step 4: Remove .git from submodule directory
if ($hasGitDir) {
    Invoke-Step "Removing .git from submodule directory" {
        Remove-Item -Recurse -Force $gitPath
    }
}

# Step 5: Remove entry from .gitmodules
if ($isSubmodule -and (Test-Path $gitmodulesPath)) {
    Invoke-Step "Removing entry from .gitmodules" {
        $content = Get-Content $gitmodulesPath -Raw
        
        # Remove the submodule section
        # Pattern matches [submodule "path"] and everything until the next [submodule or end
        $pattern = "\[submodule `"$([regex]::Escape($submodulePath))`"\][^\[]*"
        $newContent = $content -replace $pattern, ""
        
        # Clean up extra blank lines
        $newContent = $newContent -replace "`r`n`r`n`r`n+", "`r`n`r`n"
        $newContent = $newContent.TrimEnd()
        
        if ($newContent) {
            $newContent | Set-Content $gitmodulesPath -NoNewline
        }
    }
}

# Step 6: Add all files back as regular tracked files
Invoke-Step "Adding files as regular tracked content" {
    Push-Location $repoRoot
    git add $submodulePath
    Pop-Location
}

# Step 7: Commit the changes
Invoke-Step "Committing changes" {
    Push-Location $repoRoot
    git add .gitmodules 2>$null
    git commit -m "Convert $name from submodule to regular directory"
    Pop-Location
} -IgnoreError

# Step 8: Delete remote repo if requested
if ($DeleteRemoteRepo) {
    Write-Host ""
    Write-Host "WARNING: About to delete remote repository $GitHubUser/$repoName" -ForegroundColor Red
    
    if (-not $Force -and -not $DryRun) {
        $confirmDelete = Read-Host "Are you SURE you want to delete the remote repo? This cannot be undone! (type 'DELETE' to confirm)"
        if ($confirmDelete -ne "DELETE") {
            Write-Host "Skipping remote repository deletion." -ForegroundColor Yellow
        } else {
            Invoke-Step "Deleting remote GitHub repository $GitHubUser/$repoName" {
                gh repo delete "$GitHubUser/$repoName" --yes
            }
        }
    } elseif ($DryRun) {
        Write-Host "  [DRY RUN] Would delete: gh repo delete $GitHubUser/$repoName --yes" -ForegroundColor DarkGray
    } else {
        Invoke-Step "Deleting remote GitHub repository $GitHubUser/$repoName" {
            gh repo delete "$GitHubUser/$repoName" --yes
        }
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "Complete!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "$submodulePath is now a regular tracked directory." -ForegroundColor Cyan
Write-Host ""
Write-Host "Don't forget to push the changes:" -ForegroundColor Yellow
Write-Host "  git push origin <branch>" -ForegroundColor White

