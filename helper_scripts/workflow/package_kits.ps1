<#
.SYNOPSIS
    Packages kits into kits.zip for distribution
    
.DESCRIPTION
    This is a simple packaging script that creates kits.zip from the kits directory.
    Use this when you want to test packaging locally without creating a GitHub release.
    
    For actual releases, use release_kits.ps1 instead.
    
.PARAMETER kitsPath
    Path to the kits directory. Defaults to Tools/HolocronToolset/src/toolset/kits
    
.PARAMETER outputPath
    Where to save the kits.zip file. Defaults to current directory.
    
.EXAMPLE
    .\package_kits.ps1
    Creates kits.zip in current directory
    
.EXAMPLE
    .\package_kits.ps1 -outputPath "dist/kits.zip"
    Creates kits.zip in dist directory
#>

param(
    [string]$kitsPath = "Tools/HolocronToolset/src/toolset/kits",
    [string]$outputPath = "kits.zip"
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$msg) Write-ColorOutput $msg "Green" }
function Write-Info { param([string]$msg) Write-ColorOutput $msg "Cyan" }
function Write-Error { param([string]$msg) Write-ColorOutput $msg "Red" }

Write-Info "=== Kits Packager ==="

# Resolve paths
$kitsFullPath = Join-Path $PSScriptRoot ".." $kitsPath
$kitsFullPath = [System.IO.Path]::GetFullPath($kitsFullPath)
$outputFullPath = [System.IO.Path]::GetFullPath($outputPath)

if (-not (Test-Path $kitsFullPath)) {
    Write-Error "Kits directory not found: $kitsFullPath"
    exit 1
}

Write-Info "Source: $kitsFullPath"
Write-Info "Output: $outputFullPath"

# Remove existing zip
if (Test-Path $outputFullPath) {
    Remove-Item $outputFullPath -Force
    Write-Info "Removed existing zip"
}

# Create zip using .NET
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($outputFullPath, [System.IO.Compression.ZipArchiveMode]::Create)

try {
    $kitsDir = Get-Item $kitsFullPath
    $items = Get-ChildItem -Path $kitsFullPath | Where-Object {
        ($_.PSIsContainer) -or
        ($_.Extension -eq ".json" -and $_.Name -ne "available_kits.json")
    }
    
    if ($items.Count -eq 0) {
        Write-Error "No kits found to package"
        exit 1
    }
    
    Write-Info ""
    Write-Info "Packaging kits..."
    
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

$zipSize = (Get-Item $outputFullPath).Length / 1MB
Write-Success ""
Write-Success "✓ Created kits.zip ($([math]::Round($zipSize, 2)) MB)"
Write-Info "Location: $outputFullPath"

