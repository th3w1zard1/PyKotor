# KOTOR Unpacking Workflow Script
# This PowerShell script automates the unpacking workflow using both
# the Python unpacker and Scylla for IAT fixing.

param(
    [string]$KotorExePath = "",
    [string]$OutputPath = "swkotor_unpacked.exe",
    [string]$ScyllaPath = "",
    [switch]$SkipScylla
)

Write-Host "=== KOTOR Unpacking Workflow ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if KOTOR is running
Write-Host "[1/3] Checking for KOTOR process..." -ForegroundColor Yellow
$kotorProcess = Get-Process -Name "swkotor" -ErrorAction SilentlyContinue

if (-not $kotorProcess) {
    Write-Host "ERROR: KOTOR is not running!" -ForegroundColor Red
    Write-Host "Please start the game and reach the main menu, then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Found KOTOR process: PID $($kotorProcess.Id)" -ForegroundColor Green

# Step 2: Dump with Python script
Write-Host ""
Write-Host "[2/3] Dumping process memory..." -ForegroundColor Yellow

if (-not $KotorExePath) {
    # Try to find KOTOR EXE
    $possiblePaths = @(
        "$env:ProgramFiles\Steam\steamapps\common\swkotor\swkotor.exe",
        "$env:ProgramFiles(x86)\Steam\steamapps\common\swkotor\swkotor.exe",
        "$env:LOCALAPPDATA\Programs\GOG Galaxy\Games\Star Wars - Knights of the Old Republic\swkotor.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $KotorExePath = $path
            break
        }
    }
    
    if (-not $KotorExePath) {
        Write-Host "ERROR: Could not find swkotor.exe automatically." -ForegroundColor Red
        Write-Host "Please specify --KotorExePath" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Using EXE: $KotorExePath" -ForegroundColor Cyan

# Run Python unpacker
$pythonScript = Join-Path $PSScriptRoot "kotor_drm_unpacker.py"
$dumpOutput = $OutputPath -replace '\.exe$', '_raw_dump.exe'

python $pythonScript unpack --exe $KotorExePath --output $dumpOutput

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Dumping failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Dump created: $dumpOutput" -ForegroundColor Green

# Step 3: Fix IAT with Scylla (if available)
if (-not $SkipScylla) {
    Write-Host ""
    Write-Host "[3/3] Fixing IAT..." -ForegroundColor Yellow
    
    if (-not $ScyllaPath) {
        # Try to find Scylla
        $scyllaPaths = @(
            "$PSScriptRoot\Scylla\Scylla.exe",
            "$env:USERPROFILE\Downloads\Scylla\Scylla.exe",
            "$env:ProgramFiles\Scylla\Scylla.exe"
        )
        
        foreach ($path in $scyllaPaths) {
            if (Test-Path $path) {
                $ScyllaPath = $path
                break
            }
        }
    }
    
    if ($ScyllaPath -and (Test-Path $ScyllaPath)) {
        Write-Host "Using Scylla: $ScyllaPath" -ForegroundColor Cyan
        Write-Host "Opening Scylla - please:" -ForegroundColor Yellow
        Write-Host "  1. Click 'IAT Autosearch'" -ForegroundColor Yellow
        Write-Host "  2. Click 'Get Imports'" -ForegroundColor Yellow
        Write-Host "  3. Click 'Fix Dump' and save as: $OutputPath" -ForegroundColor Yellow
        Write-Host ""
        
        Start-Process $ScyllaPath -ArgumentList "`"$dumpOutput`""
        
        Write-Host "Press Enter after you've fixed the dump in Scylla..." -ForegroundColor Cyan
        Read-Host
        
        if (Test-Path $OutputPath) {
            Write-Host "Fixed dump saved: $OutputPath" -ForegroundColor Green
            Write-Host "You can now delete the raw dump: $dumpOutput" -ForegroundColor Yellow
        } else {
            Write-Host "WARNING: Fixed dump not found. Using raw dump." -ForegroundColor Yellow
            $OutputPath = $dumpOutput
        }
    } else {
        Write-Host "Scylla not found. Skipping IAT fix." -ForegroundColor Yellow
        Write-Host "You can manually fix the IAT using Scylla:" -ForegroundColor Yellow
        Write-Host "  1. Download from: https://github.com/NtQuery/Scylla/releases" -ForegroundColor Yellow
        Write-Host "  2. Open $dumpOutput in Scylla" -ForegroundColor Yellow
        Write-Host "  3. IAT Autosearch → Get Imports → Fix Dump" -ForegroundColor Yellow
        $OutputPath = $dumpOutput
    }
} else {
    Write-Host "Skipping Scylla (--SkipScylla specified)" -ForegroundColor Yellow
    $OutputPath = $dumpOutput
}

Write-Host ""
Write-Host "=== Unpacking Complete ===" -ForegroundColor Green
Write-Host "Unpacked executable: $OutputPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Import $OutputPath into Ghidra" -ForegroundColor White
Write-Host "  2. Run auto-analysis" -ForegroundColor White
Write-Host "  3. Run scripts/ghidra_kotor_apply.py to apply function names" -ForegroundColor White

