<#
.SYNOPSIS
    Creates standalone GitHub repositories for all PyKotor Tools and Libraries.

.DESCRIPTION
    Batch processes all directories in Tools/ and Libraries/ to:
    1. Create GitHub repositories for each
    2. Configure them as git submodules
    3. Update .gitmodules accordingly

.PARAMETER Type
    What to process: 'Tools', 'Libraries', or 'All'. Defaults to 'All'.

.PARAMETER GitHubUser
    The GitHub username/organization. Defaults to 'th3w1zard1'.

.PARAMETER Exclude
    Array of folder names to exclude from processing.

.PARAMETER DryRun
    Shows what would be done without making changes.

.PARAMETER Force
    Skips confirmation prompts.

.EXAMPLE
    .\create_all_submodule_repos.ps1 -DryRun
    Shows what would be done for all Tools and Libraries.

.EXAMPLE
    .\create_all_submodule_repos.ps1 -Type Tools -Exclude @("KotorMCP")
    Processes all Tools except KotorMCP.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('Tools', 'Libraries', 'All')]
    [string]$Type = 'All',

    [Parameter(Mandatory = $false)]
    [string]$GitHubUser = "th3w1zard1",

    [Parameter(Mandatory = $false)]
    [string[]]$Exclude = @("logs", "*.egg-info", "__pycache__"),

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

$scriptDir = $PSScriptRoot
$repoRoot = Split-Path -Parent $scriptDir

# Validate we're in the right place
if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
    Write-Error "Cannot find PyKotor repository root."
    exit 1
}

$createScript = Join-Path $scriptDir "create_submodule_repo.ps1"
if (-not (Test-Path $createScript)) {
    Write-Error "Cannot find create_submodule_repo.ps1 in scripts folder."
    exit 1
}

# Known special cases (repos with different names)
$specialCases = @{
    "PyKotor" = "pykotor-lib"  # Libraries/PyKotor -> th3w1zard1/pykotor-lib
}

# Collect directories to process
$toProcess = @()

if ($Type -eq 'Tools' -or $Type -eq 'All') {
    $toolsDir = Join-Path $repoRoot "Tools"
    if (Test-Path $toolsDir) {
        Get-ChildItem $toolsDir -Directory | ForEach-Object {
            $skip = $false
            foreach ($pattern in $Exclude) {
                if ($_.Name -like $pattern) { $skip = $true; break }
            }
            # Must have pyproject.toml to be considered a valid project
            $hasPyProject = Test-Path (Join-Path $_.FullName "pyproject.toml")
            if (-not $skip -and $hasPyProject) {
                $toProcess += @{
                    Category = "Tool"
                    Name = $_.Name
                    Path = $_.FullName
                }
            } elseif (-not $skip -and -not $hasPyProject) {
                Write-Host "  Skipping $($_.Name) - no pyproject.toml found" -ForegroundColor DarkGray
            }
        }
    }
}

if ($Type -eq 'Libraries' -or $Type -eq 'All') {
    $libsDir = Join-Path $repoRoot "Libraries"
    if (Test-Path $libsDir) {
        Get-ChildItem $libsDir -Directory | ForEach-Object {
            $skip = $_.Name -eq "Utility"  # Skip Utility as it's part of PyKotor
            foreach ($pattern in $Exclude) {
                if ($_.Name -like $pattern) { $skip = $true; break }
            }
            # Must have pyproject.toml to be considered a valid project
            $hasPyProject = Test-Path (Join-Path $_.FullName "pyproject.toml")
            if (-not $skip -and $hasPyProject) {
                $toProcess += @{
                    Category = "Library"
                    Name = $_.Name
                    Path = $_.FullName
                }
            } elseif (-not $skip -and -not $hasPyProject) {
                Write-Host "  Skipping $($_.Name) - no pyproject.toml found" -ForegroundColor DarkGray
            }
        }
    }
}

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "PyKotor Batch Submodule Repository Creator" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Found $($toProcess.Count) directories to process:" -ForegroundColor Yellow
Write-Host ""

foreach ($item in $toProcess) {
    $repoName = if ($specialCases.ContainsKey($item.Name)) { $specialCases[$item.Name] } else { $item.Name }
    Write-Host "  [$($item.Category)] $($item.Name) -> $GitHubUser/$repoName" -ForegroundColor White
}

Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN MODE]" -ForegroundColor Magenta
    Write-Host ""
}

if (-not $Force -and -not $DryRun) {
    $confirm = Read-Host "Proceed with processing all directories? (y/N)"
    if ($confirm -notmatch "^[Yy]") {
        Write-Host "Aborted by user." -ForegroundColor Yellow
        exit 0
    }
}

$results = @{
    Success = @()
    Failed = @()
    Skipped = @()
}

foreach ($item in $toProcess) {
    Write-Host ""
    Write-Host "=" * 50 -ForegroundColor Blue
    Write-Host "Processing: $($item.Name)" -ForegroundColor Blue
    Write-Host "=" * 50 -ForegroundColor Blue
    
    $repoName = if ($specialCases.ContainsKey($item.Name)) { $specialCases[$item.Name] } else { $item.Name }
    
    $params = @{
        GitHubUser = $GitHubUser
        RepoName = $repoName
        Force = $true
    }
    
    if ($item.Category -eq "Tool") {
        $params["Tool"] = $item.Name
    } else {
        $params["Library"] = $item.Name
    }
    
    if ($DryRun) {
        $params["DryRun"] = $true
    }
    
    try {
        & $createScript @params
        
        if ($LASTEXITCODE -eq 0) {
            $results.Success += $item.Name
        } else {
            $results.Failed += $item.Name
        }
    }
    catch {
        Write-Host "Error processing $($item.Name): $_" -ForegroundColor Red
        $results.Failed += $item.Name
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Successful: $($results.Success.Count)" -ForegroundColor Green
if ($results.Success.Count -gt 0) {
    $results.Success | ForEach-Object { Write-Host "  - $_" -ForegroundColor Green }
}

if ($results.Failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed: $($results.Failed.Count)" -ForegroundColor Red
    $results.Failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}

Write-Host ""
Write-Host "Don't forget to push the main repository:" -ForegroundColor Yellow
Write-Host "  git push origin main" -ForegroundColor White

