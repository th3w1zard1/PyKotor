<#
.SYNOPSIS
    Removes all Tool/Library submodules and converts them back to regular tracked directories.

.DESCRIPTION
    Batch processes all submodules in Tools/ and Libraries/ to convert them back to
    regular tracked directories. This is the inverse of create_all_submodule_repos.ps1.

.PARAMETER Type
    What to process: 'Tools', 'Libraries', or 'All'. Defaults to 'All'.

.PARAMETER DeleteRemoteRepos
    If specified, also deletes the remote GitHub repositories.
    USE WITH EXTREME CAUTION - this is destructive and irreversible!

.PARAMETER GitHubUser
    The GitHub username/organization. Defaults to 'th3w1zard1'.

.PARAMETER Exclude
    Array of folder names to exclude from processing.

.PARAMETER DryRun
    Shows what would be done without making changes.

.PARAMETER Force
    Skips confirmation prompts.

.EXAMPLE
    .\remove_all_submodule_repos.ps1 -DryRun
    Shows what would be done for all Tools and Libraries.

.EXAMPLE
    .\remove_all_submodule_repos.ps1 -Type Tools
    Removes all Tool submodules (keeps Libraries as submodules).

.EXAMPLE
    .\remove_all_submodule_repos.ps1 -Force
    Removes all submodules without prompting.

.EXAMPLE
    .\remove_all_submodule_repos.ps1 -DeleteRemoteRepos -Force
    Removes all submodules AND deletes all remote repos (DANGEROUS!).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('Tools', 'Libraries', 'All')]
    [string]$Type = 'All',

    [Parameter(Mandatory = $false)]
    [switch]$DeleteRemoteRepos,

    [Parameter(Mandatory = $false)]
    [string]$GitHubUser = "th3w1zard1",

    [Parameter(Mandatory = $false)]
    [string[]]$Exclude = @(),

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

$removeScript = Join-Path $scriptDir "remove_submodule_repo.ps1"
if (-not (Test-Path $removeScript)) {
    Write-Error "Cannot find remove_submodule_repo.ps1 in scripts folder."
    exit 1
}

# Read .gitmodules to find actual submodules
$gitmodulesPath = Join-Path $repoRoot ".gitmodules"
$submodules = @()

if (Test-Path $gitmodulesPath) {
    $content = Get-Content $gitmodulesPath -Raw
    
    # Find all Tool submodules
    if ($Type -eq 'Tools' -or $Type -eq 'All') {
        $toolMatches = [regex]::Matches($content, '\[submodule "Tools/([^"]+)"\]')
        foreach ($match in $toolMatches) {
            $name = $match.Groups[1].Value
            # Skip nested submodules (like kits)
            if ($name -notmatch '/') {
                $skip = $false
                foreach ($pattern in $Exclude) {
                    if ($name -like $pattern) { $skip = $true; break }
                }
                if (-not $skip) {
                    $submodules += @{
                        Category = "Tool"
                        Name = $name
                        Path = "Tools/$name"
                    }
                }
            }
        }
    }
    
    # Find all Library submodules
    if ($Type -eq 'Libraries' -or $Type -eq 'All') {
        $libMatches = [regex]::Matches($content, '\[submodule "Libraries/([^"]+)"\]')
        foreach ($match in $libMatches) {
            $name = $match.Groups[1].Value
            # Skip nested paths
            if ($name -notmatch '/') {
                $skip = $false
                foreach ($pattern in $Exclude) {
                    if ($name -like $pattern) { $skip = $true; break }
                }
                if (-not $skip) {
                    $submodules += @{
                        Category = "Library"
                        Name = $name
                        Path = "Libraries/$name"
                    }
                }
            }
        }
    }
}

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "PyKotor Batch Submodule Remover (Inverse Operation)" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

if ($submodules.Count -eq 0) {
    Write-Host "No submodules found to process." -ForegroundColor Yellow
    Write-Host "The Tools and Libraries directories are already regular tracked directories."
    exit 0
}

Write-Host "Found $($submodules.Count) submodules to convert:" -ForegroundColor Yellow
Write-Host ""

foreach ($item in $submodules) {
    Write-Host "  [$($item.Category)] $($item.Name)" -ForegroundColor White
}

Write-Host ""

if ($DeleteRemoteRepos) {
    Write-Host "WARNING: -DeleteRemoteRepos is set!" -ForegroundColor Red
    Write-Host "This will DELETE all remote GitHub repositories!" -ForegroundColor Red
    Write-Host ""
}

if ($DryRun) {
    Write-Host "[DRY RUN MODE]" -ForegroundColor Magenta
    Write-Host ""
}

if (-not $Force -and -not $DryRun) {
    Write-Host "This will convert all listed submodules to regular tracked directories." -ForegroundColor Yellow
    if ($DeleteRemoteRepos) {
        Write-Host "AND DELETE ALL REMOTE REPOSITORIES!" -ForegroundColor Red
    }
    Write-Host ""
    $confirm = Read-Host "Proceed? (y/N)"
    if ($confirm -notmatch "^[Yy]") {
        Write-Host "Aborted by user." -ForegroundColor Yellow
        exit 0
    }
    
    if ($DeleteRemoteRepos) {
        $confirmDelete = Read-Host "Type 'DELETE ALL' to confirm remote repository deletion"
        if ($confirmDelete -ne "DELETE ALL") {
            Write-Host "Remote deletion cancelled. Will only convert submodules locally." -ForegroundColor Yellow
            $DeleteRemoteRepos = $false
        }
    }
}

$results = @{
    Success = @()
    Failed = @()
}

foreach ($item in $submodules) {
    Write-Host ""
    Write-Host "=" * 50 -ForegroundColor Blue
    Write-Host "Processing: $($item.Name)" -ForegroundColor Blue
    Write-Host "=" * 50 -ForegroundColor Blue
    
    $params = @{
        GitHubUser = $GitHubUser
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
    
    if ($DeleteRemoteRepos) {
        $params["DeleteRemoteRepo"] = $true
    }
    
    try {
        & $removeScript @params
        
        if ($LASTEXITCODE -eq 0 -or $DryRun) {
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
Write-Host "All Tools and Libraries are now regular tracked directories." -ForegroundColor Green
Write-Host ""
Write-Host "Don't forget to push the changes:" -ForegroundColor Yellow
Write-Host "  git push origin <branch>" -ForegroundColor White

