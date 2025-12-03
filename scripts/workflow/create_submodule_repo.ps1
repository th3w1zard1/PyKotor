<#
.SYNOPSIS
    Creates a standalone GitHub repository for a PyKotor Tool or Library and configures it as a submodule.

.DESCRIPTION
    This script automates the process of:
    1. Creating a new GitHub repository for a Tool or Library
    2. Initializing git in the local directory
    3. Pushing the initial commit
    4. Adding the directory as a git submodule in the main PyKotor repository
    5. Updating .gitmodules with the new submodule entry

.PARAMETER Tool
    The name of the tool (folder name in Tools/) to create a repo for.
    Mutually exclusive with -Library.

.PARAMETER Library
    The name of the library (folder name in Libraries/) to create a repo for.
    Mutually exclusive with -Tool.

.PARAMETER RepoName
    Optional: Override the GitHub repository name. Defaults to the tool/library folder name.

.PARAMETER GitHubUser
    The GitHub username/organization to create the repo under. Defaults to 'th3w1zard1'.

.PARAMETER Private
    If specified, creates a private repository instead of public.

.PARAMETER DryRun
    If specified, shows what would be done without making any changes.

.PARAMETER Force
    If specified, skips confirmation prompts.

.PARAMETER SkipSubmodule
    If specified, only creates the repo without adding it as a submodule.

.EXAMPLE
    .\create_submodule_repo.ps1 -Tool HolocronToolset
    Creates a repo for Tools/HolocronToolset and adds it as a submodule.

.EXAMPLE
    .\create_submodule_repo.ps1 -Library PyKotorGL -RepoName pykotorgl-lib
    Creates a repo named 'pykotorgl-lib' for Libraries/PyKotorGL.

.EXAMPLE
    .\create_submodule_repo.ps1 -Tool KotorCLI -DryRun
    Shows what would be done for KotorCLI without making changes.

.NOTES
    Requires: GitHub CLI (gh) to be installed and authenticated.
    Run from the PyKotor repository root directory.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false, ParameterSetName = 'Tool')]
    [string]$Tool,

    [Parameter(Mandatory = $false, ParameterSetName = 'Library')]
    [string]$Library,

    [Parameter(Mandatory = $false)]
    [string]$RepoName,

    [Parameter(Mandatory = $false)]
    [string]$GitHubUser = "th3w1zard1",

    [Parameter(Mandatory = $false)]
    [switch]$Private,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$Force,

    [Parameter(Mandatory = $false)]
    [switch]$SkipSubmodule
)

# Ensure exactly one of Tool or Library is provided
if (-not $Tool -and -not $Library) {
    Write-Error "You must specify either -Tool or -Library parameter."
    Write-Host ""
    Write-Host "Usage examples:"
    Write-Host "  .\create_submodule_repo.ps1 -Tool HolocronToolset"
    Write-Host "  .\create_submodule_repo.ps1 -Library PyKotorGL"
    Write-Host "  .\create_submodule_repo.ps1 -Tool KotorCLI -DryRun"
    exit 1
}

if ($Tool -and $Library) {
    Write-Error "Cannot specify both -Tool and -Library. Choose one."
    exit 1
}

# Determine paths and names
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
    # Try current directory
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

# Validate the local path exists
if (-not (Test-Path $localPath)) {
    Write-Error "Directory not found: $localPath"
    Write-Host ""
    Write-Host "Available ${category}:"
    Get-ChildItem (Join-Path $repoRoot $category) -Directory | ForEach-Object { Write-Host "  - $($_.Name)" }
    exit 1
}

# Validate pyproject.toml exists (required for a valid project)
$pyprojectPath = Join-Path $localPath "pyproject.toml"
if (-not (Test-Path $pyprojectPath)) {
    Write-Error "pyproject.toml not found in: $localPath"
    Write-Host ""
    Write-Host "This directory does not appear to be a valid Python project."
    Write-Host "All Tools and Libraries must have a pyproject.toml file."
    exit 1
}

# Determine repo name
if (-not $RepoName) {
    $RepoName = $name
}

$repoUrl = "https://github.com/$GitHubUser/$RepoName.git"
$submodulePath = "$category/$name"
$visibility = if ($Private) { "--private" } else { "--public" }

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "PyKotor Submodule Repository Creator" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Category:       $category"
Write-Host "  Name:           $name"
Write-Host "  Local Path:     $localPath"
Write-Host "  GitHub User:    $GitHubUser"
Write-Host "  Repo Name:      $RepoName"
Write-Host "  Repo URL:       $repoUrl"
Write-Host "  Submodule Path: $submodulePath"
Write-Host "  Visibility:     $(if ($Private) { 'Private' } else { 'Public' })"
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN MODE - No changes will be made]" -ForegroundColor Magenta
    Write-Host ""
}

# Check if gh CLI is available
$ghPath = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghPath) {
    Write-Error "GitHub CLI (gh) is not installed or not in PATH."
    Write-Host "Install it from: https://cli.github.com/"
    exit 1
}

# Check gh authentication
$ghAuth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "GitHub CLI is not authenticated. Run 'gh auth login' first."
    exit 1
}

# Function to run commands (respects DryRun)
function Invoke-Step {
    param(
        [string]$Description,
        [scriptblock]$Action,
        [switch]$Critical
    )
    
    Write-Host "→ $Description" -ForegroundColor Green
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would execute: $($Action.ToString().Trim())" -ForegroundColor DarkGray
        return $true
    }
    
    try {
        & $Action
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
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

# Check if repo already exists on GitHub
Write-Host "Checking if repository already exists on GitHub..." -ForegroundColor Yellow
$repoExists = $false
try {
    $existingRepo = gh repo view "$GitHubUser/$RepoName" --json name 2>$null
    if ($LASTEXITCODE -eq 0) {
        $repoExists = $true
        Write-Host "  Repository $GitHubUser/$RepoName already exists on GitHub." -ForegroundColor Yellow
    }
}
catch {
    # Repo doesn't exist, that's fine
}

# Check if already a git repo
$isGitRepo = Test-Path (Join-Path $localPath ".git")
if ($isGitRepo) {
    Write-Host "  Directory is already a git repository." -ForegroundColor Yellow
}

# Check if already in .gitmodules
$gitmodulesPath = Join-Path $repoRoot ".gitmodules"
$isSubmodule = $false
if (Test-Path $gitmodulesPath) {
    $gitmodulesContent = Get-Content $gitmodulesPath -Raw
    if ($gitmodulesContent -match [regex]::Escape("path = $submodulePath")) {
        $isSubmodule = $true
        Write-Host "  Already listed in .gitmodules." -ForegroundColor Yellow
    }
}

# Confirm action
if (-not $Force -and -not $DryRun) {
    Write-Host ""
    $confirm = Read-Host "Proceed with creating/updating repository? (y/N)"
    if ($confirm -notmatch "^[Yy]") {
        Write-Host "Aborted by user." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "Executing steps..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Initialize git if needed
if (-not $isGitRepo) {
    Invoke-Step "Initializing git repository in $localPath" {
        Push-Location $localPath
        git init
        Pop-Location
    } -Critical
}

# Step 2: Add all files and commit
Invoke-Step "Adding files and creating initial commit" {
    Push-Location $localPath
    git add .
    $commitResult = git commit -m "Initial commit - $name" 2>&1
    # Commit may fail if nothing to commit, that's okay
    Pop-Location
}

# Step 3: Create GitHub repo if it doesn't exist
if (-not $repoExists) {
    Invoke-Step "Creating GitHub repository $GitHubUser/$RepoName" {
        Push-Location $localPath
        gh repo create "$GitHubUser/$RepoName" $visibility --source . --remote origin --push
        Pop-Location
    } -Critical
} else {
    # Repo exists, just add remote and push
    Invoke-Step "Adding remote and pushing to existing repository" {
        Push-Location $localPath
        $remotes = git remote 2>$null
        if ($remotes -notcontains "origin") {
            git remote add origin $repoUrl
        }
        git push -u origin HEAD 2>&1
        Pop-Location
    }
}

# Step 4: Add as submodule to main repo (if not already)
if (-not $SkipSubmodule -and -not $isSubmodule) {
    Invoke-Step "Removing local directory to prepare for submodule" {
        Push-Location $repoRoot
        # First, we need to remove the directory from git index (if tracked)
        git rm -rf --cached $submodulePath 2>$null
        Pop-Location
    }
    
    Invoke-Step "Adding as submodule to main repository" {
        Push-Location $repoRoot
        git submodule add $repoUrl $submodulePath
        Pop-Location
    } -Critical
    
    Invoke-Step "Committing submodule addition" {
        Push-Location $repoRoot
        git add .gitmodules $submodulePath
        git commit -m "Add $name as submodule"
        Pop-Location
    }
}

# Step 5: Update pyproject.toml for uvx compatibility (if needed)
$pyprojectPath = Join-Path $localPath "pyproject.toml"
if (Test-Path $pyprojectPath) {
    Write-Host ""
    Write-Host "Checking pyproject.toml for uvx compatibility..." -ForegroundColor Yellow
    
    $pyprojectContent = Get-Content $pyprojectPath -Raw
    $needsUpdate = $false
    $updates = @()
    
    # Check for relative readme paths
    if ($pyprojectContent -match 'readme\s*=.*\.\./') {
        $needsUpdate = $true
        $updates += "- Contains relative readme path (../../README.md)"
    }
    
    # Check for pykotor dependency pointing to PyPI (outdated)
    if ($pyprojectContent -match '"pykotor>=') {
        $updates += "- Consider updating pykotor dependency to git URL for uvx compatibility"
    }
    
    if ($updates.Count -gt 0) {
        Write-Host "  pyproject.toml notes:" -ForegroundColor Yellow
        $updates | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkYellow }
        Write-Host ""
        Write-Host "  For uvx compatibility, you may need to:" -ForegroundColor Cyan
        Write-Host "    1. Create a local README.md in the repo" -ForegroundColor Cyan
        Write-Host "    2. Update pykotor dependency to:" -ForegroundColor Cyan
        Write-Host '       pykotor = { git = "https://github.com/th3w1zard1/pykotor-lib.git" }' -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "Complete!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "Repository: https://github.com/$GitHubUser/$RepoName" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run with uvx:" -ForegroundColor Yellow
$packageName = $name.ToLower()
Write-Host "  uvx --from `"$packageName @ git+https://github.com/$GitHubUser/$RepoName.git`" $packageName" -ForegroundColor White
Write-Host ""

if (-not $SkipSubmodule) {
    Write-Host "Submodule added. Don't forget to push the main repo:" -ForegroundColor Yellow
    Write-Host "  git push origin main" -ForegroundColor White
}

