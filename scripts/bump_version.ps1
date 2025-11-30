<#
.SYNOPSIS
    Bumps version for a PyKotor tool and optionally creates a release.

.DESCRIPTION
    This script updates the version in the tool's config file, validates the change,
    and optionally commits/pushes and creates a GitHub pre-release.

.PARAMETER Tool
    The tool to bump version for: toolset, holopatcher, kotordiff, guiconverter

.PARAMETER Version
    The new version (e.g., 3.1.3 or 1.8.0)

.PARAMETER Commit
    If specified, commits and pushes the version change

.PARAMETER CreateRelease
    If specified, creates a GitHub pre-release after committing

.PARAMETER DryRun
    If specified, shows what would be changed without making changes

.EXAMPLE
    .\bump_version.ps1 -Tool toolset -Version 3.1.3 -DryRun
    Shows what would be changed without making changes

.EXAMPLE
    .\bump_version.ps1 -Tool toolset -Version 3.1.3 -Commit
    Updates version and commits to the current branch

.EXAMPLE
    .\bump_version.ps1 -Tool toolset -Version 3.1.3 -Commit -CreateRelease
    Updates version, commits, and creates a GitHub pre-release
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("toolset", "holopatcher", "kotordiff", "guiconverter", "batchpatcher", "kitgenerator")]
    [string]$Tool,
    
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [switch]$Commit,
    [switch]$CreateRelease,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Determine project root
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot

# Tool configuration
$ToolConfig = @{
    "toolset" = @{
        ConfigFile = "Tools/HolocronToolset/src/toolset/config.py"
        VersionKey = "currentVersion"
        TagPattern = "v{0}-toolset"
        LatestKey = "toolsetLatestVersion"
        BetaKey = "toolsetLatestBetaVersion"
    }
    "holopatcher" = @{
        ConfigFile = "Tools/HoloPatcher/src/holopatcher/config.py"
        VersionKey = "currentVersion"
        TagPattern = "v{0}-patcher"
        LatestKey = "holopatcherLatestVersion"
        BetaKey = "holopatcherLatestBetaVersion"
    }
    "kotordiff" = @{
        ConfigFile = "Tools/KotorDiff/src/kotordiff/__main__.py"
        VersionKey = "CURRENT_VERSION"
        TagPattern = "v{0}-kotordiff"
    }
    "guiconverter" = @{
        ConfigFile = "Tools/GuiConverter/src/gui_converter/__init__.py"
        VersionKey = "__version__"
        TagPattern = "v{0}-guiconverter"
    }
    "batchpatcher" = @{
        ConfigFile = "Tools/BatchPatcher/src/batchpatcher/__init__.py"
        VersionKey = "__version__"
        TagPattern = "v{0}-batchpatcher"
    }
    "kitgenerator" = @{
        ConfigFile = "Tools/KitGenerator/src/kitgenerator/__init__.py"
        VersionKey = "__version__"
        TagPattern = "v{0}-kitgenerator"
    }
}

$Config = $ToolConfig[$Tool]
$ConfigFilePath = Join-Path $ProjectRoot $Config.ConfigFile
$TagName = $Config.TagPattern -f $Version

Write-Host ""
Write-Host "=== Version Bump for $Tool ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Version:     $Version"
Write-Host "  Config File: $($Config.ConfigFile)"
Write-Host "  Tag Name:    $TagName"
Write-Host ""

# Validate version format
if ($Version -notmatch '^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9.]+)?$') {
    Write-Host "❌ Invalid version format: $Version" -ForegroundColor Red
    Write-Host "   Expected: MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH-suffix"
    exit 1
}
Write-Host "✓ Version format is valid" -ForegroundColor Green

# Check config file exists
if (-not (Test-Path $ConfigFilePath)) {
    Write-Host "❌ Config file not found: $ConfigFilePath" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Config file exists" -ForegroundColor Green

# Read current version
$ConfigContent = Get-Content $ConfigFilePath -Raw

$CurrentVersion = $null
if ($Config.VersionKey -eq "CURRENT_VERSION") {
    # Python variable assignment style
    if ($ConfigContent -match 'CURRENT_VERSION\s*=\s*"([^"]+)"') {
        $CurrentVersion = $matches[1]
    }
} elseif ($Config.VersionKey -eq "__version__") {
    # __version__ style
    if ($ConfigContent -match '__version__\s*=\s*"([^"]+)"') {
        $CurrentVersion = $matches[1]
    }
} else {
    # JSON-style in LOCAL_PROGRAM_INFO
    if ($ConfigContent -match '"currentVersion":\s*"([^"]+)"') {
        $CurrentVersion = $matches[1]
    }
}

if ($CurrentVersion) {
    Write-Host "  Current version: $CurrentVersion"
} else {
    Write-Host "⚠️  Could not detect current version" -ForegroundColor Yellow
}

if ($CurrentVersion -eq $Version) {
    Write-Host ""
    Write-Host "⚠️  Version is already set to $Version" -ForegroundColor Yellow
    if (-not $Commit -and -not $CreateRelease) {
        exit 0
    }
}

Write-Host ""

# Prepare the updated content
$NewContent = $ConfigContent
if ($Config.VersionKey -eq "CURRENT_VERSION") {
    $NewContent = $ConfigContent -replace 'CURRENT_VERSION\s*=\s*"[^"]+"', "CURRENT_VERSION = `"$Version`""
} elseif ($Config.VersionKey -eq "__version__") {
    $NewContent = $ConfigContent -replace '__version__\s*=\s*"[^"]+"', "__version__ = `"$Version`""
} else {
    $NewContent = $ConfigContent -replace '"currentVersion":\s*"[^"]+"', "`"currentVersion`": `"$Version`""
}

if ($DryRun) {
    Write-Host "=== DRY RUN MODE ===" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Would update $($Config.ConfigFile):"
    Write-Host "  $($Config.VersionKey): $CurrentVersion -> $Version"
    Write-Host ""
    
    if ($Commit) {
        Write-Host "Would commit with message:"
        Write-Host "  chore($Tool): bump version to $Version"
        Write-Host ""
    }
    
    if ($CreateRelease) {
        Write-Host "Would create GitHub pre-release:"
        Write-Host "  Tag: $TagName"
        Write-Host "  Title: $Tool v$Version"
        Write-Host ""
    }
    
    Write-Host "=== DRY RUN COMPLETE ===" -ForegroundColor Yellow
    exit 0
}

# Write the updated content
Write-Host "Updating $($Config.ConfigFile)..." -ForegroundColor Cyan
Set-Content -Path $ConfigFilePath -Value $NewContent -NoNewline
Write-Host "✓ Version updated to $Version" -ForegroundColor Green

# Verify the change
$VerifyContent = Get-Content $ConfigFilePath -Raw
$VerifyMatch = $false
if ($Config.VersionKey -eq "CURRENT_VERSION") {
    $VerifyMatch = $VerifyContent -match "CURRENT_VERSION\s*=\s*`"$Version`""
} elseif ($Config.VersionKey -eq "__version__") {
    $VerifyMatch = $VerifyContent -match "__version__\s*=\s*`"$Version`""
} else {
    $VerifyMatch = $VerifyContent -match "`"currentVersion`":\s*`"$Version`""
}

if (-not $VerifyMatch) {
    Write-Host "❌ Failed to verify version update" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Version change verified" -ForegroundColor Green

if ($Commit) {
    Write-Host ""
    Write-Host "Committing changes..." -ForegroundColor Cyan
    
    Push-Location $ProjectRoot
    try {
        git add $Config.ConfigFile
        $CommitMessage = "chore($Tool): bump version to $Version"
        git commit -m $CommitMessage
        Write-Host "✓ Changes committed" -ForegroundColor Green
        
        git push
        Write-Host "✓ Changes pushed" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
}

if ($CreateRelease) {
    Write-Host ""
    Write-Host "Creating GitHub pre-release..." -ForegroundColor Cyan
    
    # Check if gh CLI is available
    $ghPath = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $ghPath) {
        Write-Host "❌ GitHub CLI (gh) not found. Install it from https://cli.github.com/" -ForegroundColor Red
        Write-Host ""
        Write-Host "Manual release instructions:" -ForegroundColor Yellow
        Write-Host "1. Go to https://github.com/NickHugi/PyKotor/releases/new"
        Write-Host "2. Create tag: $TagName"
        Write-Host "3. Title: $Tool v$Version"
        Write-Host "4. Mark as pre-release"
        Write-Host "5. Publish"
        exit 1
    }
    
    Push-Location $ProjectRoot
    try {
        # Create the tag
        git tag $TagName
        git push origin $TagName
        Write-Host "✓ Tag $TagName created and pushed" -ForegroundColor Green
        
        # Create the pre-release
        $ReleaseTitle = "$Tool v$Version"
        $ReleaseNotes = "Release $Version of $Tool.`n`nSee the workflow run for build artifacts."
        
        gh release create $TagName --prerelease --title $ReleaseTitle --notes $ReleaseNotes
        Write-Host "✓ Pre-release created: $TagName" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Failed to create release: $_" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Manual release instructions:" -ForegroundColor Yellow
        Write-Host "1. Go to https://github.com/NickHugi/PyKotor/releases/new"
        Write-Host "2. Create tag: $TagName"
        Write-Host "3. Title: $tool v$Version"
        Write-Host "4. Mark as pre-release"
        Write-Host "5. Publish"
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host ""

if (-not $Commit -and -not $CreateRelease) {
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Review the changes in $($Config.ConfigFile)"
    Write-Host "2. Commit: git add $($Config.ConfigFile) && git commit -m `"chore($Tool): bump version to $Version`""
    Write-Host "3. Push: git push"
    Write-Host "4. Create pre-release with tag: $TagName"
    Write-Host ""
    Write-Host "Or run: .\bump_version.ps1 -Tool $Tool -Version $Version -Commit -CreateRelease"
}

