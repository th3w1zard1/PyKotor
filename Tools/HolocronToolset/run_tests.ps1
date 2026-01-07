# PowerShell wrapper to run pytest with timeout
# Times out after 300 seconds (5 minutes)

$ErrorActionPreference = "Stop"

# Change to the toolset directory
$toolsetDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $toolsetDir

# Create output file for pytest results
$outputFile = Join-Path $toolsetDir "test_output.log"

# Run pytest with timeout
Write-Host "Starting pytest tests (timeout: 300 seconds)..." -ForegroundColor Cyan
$proc = Start-Process python -ArgumentList "-m", "pytest", "tests/", "-v", "--tb=short", "--durations=10" -PassThru -NoNewWindow -RedirectStandardOutput $outputFile -RedirectStandardError "$outputFile.err"

# Wait for process with 300 second timeout
$timedOut = $false
if (-not $proc.WaitForExit(300000)) {
    Write-Host "`nTIMEOUT: Tests exceeded 300 seconds, killing process..." -ForegroundColor Red
    $proc.Kill()
    $timedOut = $true
    # Wait a moment for the process to actually terminate
    Start-Sleep -Seconds 2
}

# Display output
Write-Host "`n=== Test Output ===" -ForegroundColor Cyan
if (Test-Path $outputFile) {
    Get-Content $outputFile | Write-Host
}
if (Test-Path "$outputFile.err") {
    Write-Host "`n=== Errors ===" -ForegroundColor Red
    Get-Content "$outputFile.err" | Write-Host -ForegroundColor Red
}

if ($timedOut) {
    Write-Host "`nTest output saved to: $outputFile" -ForegroundColor Yellow
    Write-Host "Please review the output to identify slow tests that should be skipped." -ForegroundColor Yellow
    exit 1
}

# Return the exit code
exit $proc.ExitCode
