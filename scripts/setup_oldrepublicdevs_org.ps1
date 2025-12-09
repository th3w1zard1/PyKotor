<#
.SYNOPSIS
    Sets up the OldRepublicDevs organization: invites NickHugi and transfers PyKotor repository.

.DESCRIPTION
    This script automates:
    1. Inviting NickHugi to OldRepublicDevs organization with owner permissions
    2. Transferring th3w1zard1/PyKotor repository to OldRepublicDevs organization

.PARAMETER OrgName
    The organization name. Defaults to 'OldRepublicDevs'.

.PARAMETER Username
    The GitHub username to invite. Defaults to 'NickHugi'.

.PARAMETER RepoOwner
    Current repository owner. Defaults to 'th3w1zard1'.

.PARAMETER RepoName
    Repository name. Defaults to 'PyKotor'.

.PARAMETER DryRun
    If specified, shows what would be done without making changes.

.EXAMPLE
    .\setup_oldrepublicdevs_org.ps1
    Invites NickHugi and transfers the repository.

.NOTES
    Requires: GitHub CLI (gh) to be installed and authenticated.
    The organization must already exist before running this script.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$OrgName = "OldRepublicDevs",

    [Parameter(Mandatory = $false)]
    [string]$Username = "NickHugi",

    [Parameter(Mandatory = $false)]
    [string]$RepoOwner = "th3w1zard1",

    [Parameter(Mandatory = $false)]
    [string]$RepoName = "PyKotor",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "Setting up OldRepublicDevs organization..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify organization exists
Write-Host "Step 1: Verifying organization '$OrgName' exists..." -ForegroundColor Yellow
try {
    $orgInfo = gh api "orgs/$OrgName" --jq '.login' 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Organization '$OrgName' does not exist or is not accessible." -ForegroundColor Red
        Write-Host "Please create the organization at: https://github.com/account/organizations/new" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✓ Organization '$OrgName' exists" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to verify organization: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Invite NickHugi with owner permissions
Write-Host "Step 2: Inviting '$Username' to organization with owner permissions..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "[DRY RUN] Would invite $Username to $OrgName with owner role" -ForegroundColor Gray
} else {
    try {
        # First, check if user is already a member
        $membership = gh api "orgs/$OrgName/memberships/$Username" --jq '.role' 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ User '$Username' is already a member (role: $membership)" -ForegroundColor Green
            if ($membership -ne "admin") {
                Write-Host "Updating role to owner..." -ForegroundColor Yellow
                gh api "orgs/$OrgName/memberships/$Username" -X PATCH -f role=admin 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✓ Updated role to owner" -ForegroundColor Green
                } else {
                    Write-Host "WARNING: Failed to update role. User may need to be invited as owner manually." -ForegroundColor Yellow
                }
            }
        } else {
            # Invite the user
            Write-Host "Inviting $Username..." -ForegroundColor Gray
            $inviteResult = gh api "orgs/$OrgName/invitations" -X POST -f invitee_id="$Username" -f role=admin 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Invitation sent to '$Username' with owner permissions" -ForegroundColor Green
            } else {
                # Try alternative API endpoint
                Write-Host "Trying alternative invitation method..." -ForegroundColor Gray
                $inviteResult = gh api "orgs/$OrgName/memberships/$Username" -X PUT -f role=admin 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✓ Added '$Username' to organization with owner permissions" -ForegroundColor Green
                } else {
                    Write-Host "WARNING: Failed to invite user via API. Error: $inviteResult" -ForegroundColor Yellow
                    Write-Host "You may need to invite manually at: https://github.com/orgs/$OrgName/people" -ForegroundColor Yellow
                }
            }
        }
    } catch {
        Write-Host "WARNING: Failed to invite user: $_" -ForegroundColor Yellow
        Write-Host "You may need to invite manually at: https://github.com/orgs/$OrgName/people" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 3: Transfer repository to organization
Write-Host "Step 3: Transferring repository '$RepoOwner/$RepoName' to '$OrgName'..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "[DRY RUN] Would transfer $RepoOwner/$RepoName to $OrgName" -ForegroundColor Gray
} else {
    try {
        # Check current repository owner
        $currentOwner = gh api "repos/$RepoOwner/$RepoName" --jq '.owner.login' 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Repository '$RepoOwner/$RepoName' not found or not accessible." -ForegroundColor Red
            exit 1
        }

        if ($currentOwner -eq $OrgName) {
            Write-Host "✓ Repository is already owned by '$OrgName'" -ForegroundColor Green
        } else {
            Write-Host "Current owner: $currentOwner" -ForegroundColor Gray
            Write-Host "Transferring to: $OrgName..." -ForegroundColor Gray
            
            # Transfer repository using GitHub API
            $transferResult = gh api "repos/$RepoOwner/$RepoName/transfer" -X POST -f new_owner="$OrgName" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Repository transfer initiated" -ForegroundColor Green
                Write-Host "Note: Repository transfers may take a few moments to complete." -ForegroundColor Gray
            } else {
                Write-Host "WARNING: Failed to transfer repository via API. Error: $transferResult" -ForegroundColor Yellow
                Write-Host "You may need to transfer manually:" -ForegroundColor Yellow
                Write-Host "  1. Go to: https://github.com/$RepoOwner/$RepoName/settings" -ForegroundColor Cyan
                Write-Host "  2. Scroll to 'Danger Zone'" -ForegroundColor Cyan
                Write-Host "  3. Click 'Transfer ownership'" -ForegroundColor Cyan
                Write-Host "  4. Enter: $OrgName" -ForegroundColor Cyan
            }
        }
    } catch {
        Write-Host "WARNING: Failed to transfer repository: $_" -ForegroundColor Yellow
        Write-Host "You may need to transfer manually at: https://github.com/$RepoOwner/$RepoName/settings" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Organization: $OrgName" -ForegroundColor White
Write-Host "  Invited user: $Username" -ForegroundColor White
Write-Host "  Repository: $RepoOwner/$RepoName -> $OrgName/$RepoName" -ForegroundColor White

