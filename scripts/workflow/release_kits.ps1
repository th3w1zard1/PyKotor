<#
.SYNOPSIS
    Creates a GitHub release for the ToolsetData repository with kits.zip
    
.DESCRIPTION
    This script packages all kits from the Tools/HolocronToolset/src/toolset/kits directory
    into a kits.zip file and creates a GitHub release in the th3w1zard1/ToolsetData repository.
    
    The script is designed to be idempotent and flexible:
    - Can create new releases or update existing ones
    - Can specify custom tag names
    - Validates kit structure before packaging
    - Uses GitHub CLI for reliable API interaction
    
.PARAMETER tag
    The release tag name (e.g., "v1.0.0"). If not specified, generates one based on kits version.
    
.PARAMETER draft
    Create the release as a draft (not publicly visible)
    
.PARAMETER prerelease
    Mark the release as a pre-release
    
.PARAMETER force
    Force recreation of the release if it already exists
    
.PARAMETER kitsPath
    Path to the kits directory. Defaults to Tools/HolocronToolset/src/toolset/kits
    
.PARAMETER repo
    GitHub repository in format "owner/repo". Defaults to "th3w1zard1/ToolsetData"
    
.EXAMPLE
    .\release_kits.ps1
    Creates a new release with auto-generated tag
    
.EXAMPLE
    .\release_kits.ps1 -tag "v1.0.0" -draft
    Creates a draft release with tag v1.0.0
    
.EXAMPLE
    .\release_kits.ps1 -tag "v1.0.0" -force
    Recreates release v1.0.0 if it exists
#>

param(
    [string]$tag = "",
    [switch]$draft,
    [switch]$prerelease,
    [switch]$force,
    [string]$kitsPath = "Tools/HolocronToolset/src/toolset/kits",
    [string]$repo = "th3w1zard1/ToolsetData"
)

$ErrorActionPreference = "Stop"

# Color output functions
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$msg) Write-ColorOutput $msg "Green" }
function Write-Info { param([string]$msg) Write-ColorOutput $msg "Cyan" }
function Write-Warning { param([string]$msg) Write-ColorOutput $msg "Yellow" }
function Write-Error { param([string]$msg) Write-ColorOutput $msg "Red" }

# Check if gh CLI is installed
function Test-GitHubCLI {
    try {
        $null = gh --version
        return $true
    }
    catch {
        Write-Error "GitHub CLI (gh) is not installed or not in PATH."
        Write-Info "Install it from: https://cli.github.com/"
        return $false
    }
}

# Validate kits directory structure
function Test-KitsStructure {
    param([string]$path)
    
    Write-Info "Validating kits directory structure..."
    
    if (-not (Test-Path $path)) {
        Write-Error "Kits directory not found: $path"
        return $false
    }
    
    $jsonFiles = Get-ChildItem -Path $path -Filter "*.json" | Where-Object { $_.Name -ne "available_kits.json" }
    
    if ($jsonFiles.Count -eq 0) {
        Write-Error "No kit JSON files found in $path"
        return $false
    }
    
    $valid = $true
    foreach ($jsonFile in $jsonFiles) {
        $kitId = $jsonFile.BaseName
        $kitDir = Join-Path $path $kitId
        
        if (-not (Test-Path $kitDir)) {
            Write-Warning "Missing directory for kit: $kitId"
            $valid = $false
            continue
        }
        
        Write-Success "✓ Found kit: $kitId"
    }
    
    return $valid
}

# Generate tag from kits versions
function Get-AutoTag {
    param([string]$path)
    
    Write-Info "Generating tag from kit versions..."
    
    $jsonFiles = Get-ChildItem -Path $path -Filter "*.json" | Where-Object { $_.Name -ne "available_kits.json" }
    $maxVersion = 1
    
    foreach ($jsonFile in $jsonFiles) {
        $json = Get-Content $jsonFile.FullName | ConvertFrom-Json
        if ($json.version -gt $maxVersion) {
            $maxVersion = $json.version
        }
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd"
    $tag = "v$maxVersion.$timestamp"
    Write-Info "Generated tag: $tag"
    return $tag
}

# Create kits.zip
function New-KitsZip {
    param(
        [string]$sourcePath,
        [string]$outputPath
    )
    
    Write-Info "Creating kits.zip..."
    
    if (Test-Path $outputPath) {
        Remove-Item $outputPath -Force
    }
    
    # Get all kit directories and JSON files
    $kitsDir = Get-Item $sourcePath
    $items = Get-ChildItem -Path $sourcePath | Where-Object {
        ($_.PSIsContainer) -or
        ($_.Extension -eq ".json" -and $_.Name -ne "available_kits.json")
    }
    
    if ($items.Count -eq 0) {
        Write-Error "No kits found to package"
        return $false
    }
    
    # Create zip using .NET
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::Open($outputPath, [System.IO.Compression.ZipArchiveMode]::Create)
    
    try {
        foreach ($item in $items) {
            if ($item.PSIsContainer) {
                # Add directory recursively
                $files = Get-ChildItem -Path $item.FullName -Recurse -File
                foreach ($file in $files) {
                    $relativePath = $file.FullName.Substring($kitsDir.FullName.Length + 1)
                    $entry = $zip.CreateEntry($relativePath.Replace('\', '/'))
                    $entryStream = $entry.Open()
                    $fileStream = [System.IO.File]::OpenRead($file.FullName)
                    $fileStream.CopyTo($entryStream)
                    $fileStream.Close()
                    $entryStream.Close()
                }
                Write-Success "  ✓ Added directory: $($item.Name)"
            }
            else {
                # Add JSON file
                $entry = $zip.CreateEntry($item.Name)
                $entryStream = $entry.Open()
                $fileStream = [System.IO.File]::OpenRead($item.FullName)
                $fileStream.CopyTo($entryStream)
                $fileStream.Close()
                $entryStream.Close()
                Write-Success "  ✓ Added file: $($item.Name)"
            }
        }
    }
    finally {
        $zip.Dispose()
    }
    
    $zipSize = (Get-Item $outputPath).Length / 1MB
    Write-Success "Created kits.zip ($([math]::Round($zipSize, 2)) MB)"
    return $true
}

# Create or update GitHub release
function New-GitHubRelease {
    param(
        [string]$repo,
        [string]$tag,
        [string]$zipPath,
        [bool]$isDraft,
        [bool]$isPrerelease,
        [bool]$forceRecreate
    )
    
    Write-Info "Creating GitHub release..."
    
    # Check if release exists
    $existingRelease = gh release view $tag --repo $repo 2>&1
    if ($LASTEXITCODE -eq 0 -and -not $forceRecreate) {
        Write-Warning "Release $tag already exists. Use -force to recreate."
        Write-Info "Uploading asset to existing release..."
        gh release upload $tag $zipPath --repo $repo --clobber
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to upload asset to existing release"
            return $false
        }
        Write-Success "Asset uploaded to existing release: $tag"
        return $true
    }
    
    if ($LASTEXITCODE -eq 0 -and $forceRecreate) {
        Write-Info "Deleting existing release $tag..."
        gh release delete $tag --repo $repo --yes
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to delete existing release"
            return $false
        }
    }
    
    # Build release command
    $releaseArgs = @(
        "release", "create", $tag,
        $zipPath,
        "--repo", $repo,
        "--title", "Kits Release $tag",
        "--notes", "Automated release of HolocronToolset kits`n`nContains all available map builder kits."
    )
    
    if ($isDraft) {
        $releaseArgs += "--draft"
    }
    
    if ($isPrerelease) {
        $releaseArgs += "--prerelease"
    }
    
    # Create release
    Write-Info "Executing: gh $($releaseArgs -join ' ')"
    & gh @releaseArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create release"
        return $false
    }
    
    Write-Success "Release created successfully: $tag"
    return $true
}

# Main execution
function Main {
    Write-Info "=== Kits Release Manager ==="
    Write-Info ""
    
    # Check prerequisites
    if (-not (Test-GitHubCLI)) {
        exit 1
    }
    
    # Validate kits structure
    $kitsFullPath = Join-Path $PSScriptRoot ".." $kitsPath
    $kitsFullPath = [System.IO.Path]::GetFullPath($kitsFullPath)
    
    if (-not (Test-KitsStructure $kitsFullPath)) {
        Write-Error "Kit structure validation failed"
        exit 1
    }
    
    # Generate tag if not provided
    if ([string]::IsNullOrEmpty($tag)) {
        $tag = Get-AutoTag $kitsFullPath
    }
    
    Write-Info "Release configuration:"
    Write-Info "  Repository: $repo"
    Write-Info "  Tag: $tag"
    Write-Info "  Draft: $draft"
    Write-Info "  Prerelease: $prerelease"
    Write-Info "  Force: $force"
    Write-Info ""
    
    # Create temporary directory for zip
    $tempDir = Join-Path $env:TEMP "kits_release_$(Get-Date -Format 'yyyyMMddHHmmss')"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    $zipPath = Join-Path $tempDir "kits.zip"
    
    try {
        # Create kits.zip
        if (-not (New-KitsZip -sourcePath $kitsFullPath -outputPath $zipPath)) {
            exit 1
        }
        
        # Create GitHub release
        if (-not (New-GitHubRelease -repo $repo -tag $tag -zipPath $zipPath -isDraft $draft -isPrerelease $prerelease -forceRecreate $force)) {
            exit 1
        }
        
        Write-Success ""
        Write-Success "=== Release completed successfully! ==="
        Write-Info "View release: https://github.com/$repo/releases/tag/$tag"
    }
    finally {
        # Cleanup
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force
        }
    }
}

# Run main function
Main

