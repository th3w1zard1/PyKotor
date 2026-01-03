#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Git commit with automatic pre-commit fix staging and retry.

.DESCRIPTION
    Runs git commit, and if pre-commit hooks fail due to auto-fixes,
    automatically stages the fixes and retries the commit.

.PARAMETER Message
    Commit message

.PARAMETER Files
    Optional list of files to stage before committing. If not provided, uses all staged files.

.EXAMPLE
    .\scripts\git-commit-with-auto-fix.ps1 -Message "fix: something"

.EXAMPLE
    .\scripts\git-commit-with-auto-fix.ps1 -Message "feat: new feature" -Files "file1.py", "file2.py"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Message,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Files = @()
)

$maxRetries = 3
$retryCount = 0

function Commit-WithRetry {
    param([string]$CommitMessage, [string[]]$FilesToStage)

    if ($FilesToStage.Count -gt 0) {
        Write-Host "Staging files: $($FilesToStage -join ', ')" -ForegroundColor Cyan
        git add $FilesToStage
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to stage files" -ForegroundColor Red
            exit 1
        }
    }

    Write-Host "Committing with message: $CommitMessage" -ForegroundColor Cyan
    $commitOutput = git commit -m $CommitMessage 2>&1
    $commitExitCode = $LASTEXITCODE

    # Check if commit succeeded
    if ($commitExitCode -eq 0) {
        Write-Host "Commit successful!" -ForegroundColor Green
        return $true
    }

    # Check if pre-commit hooks modified files (look for "files were modified" in output)
    $outputText = $commitOutput -join "`n"
    if ($outputText -match "files were modified by this hook" -or $outputText -match "fixed") {
        Write-Host "`nPre-commit hooks made automatic fixes. Staging fixes and retrying..." -ForegroundColor Yellow

        # Get list of modified files
        $modifiedFiles = git diff --name-only
        if ($modifiedFiles.Count -eq 0) {
            # Also check staged changes
            $modifiedFiles = git diff --cached --name-only
        }

        if ($modifiedFiles.Count -gt 0) {
            Write-Host "Staging auto-fixes: $($modifiedFiles -join ', ')" -ForegroundColor Cyan
            git add $modifiedFiles
            return $false  # Indicates we should retry
        }
    }

    # If we get here, commit failed for a different reason
    Write-Host "`nCommit failed (not due to auto-fixes):" -ForegroundColor Red
    Write-Host $outputText
    return $false
}

# Main commit loop
do {
    $success = Commit-WithRetry -CommitMessage $Message -FilesToStage $Files
    $retryCount++

    if (-not $success -and $retryCount -lt $maxRetries) {
        Write-Host "Retrying commit (attempt $retryCount of $maxRetries)..." -ForegroundColor Yellow
        Start-Sleep -Milliseconds 500
    } elseif (-not $success) {
        Write-Host "`nFailed after $maxRetries attempts. Manual intervention required." -ForegroundColor Red
        exit 1
    }
} while (-not $success -and $retryCount -lt $maxRetries)
