# Transfer NickHugi/PyKotor to OldRepublicDevs

## Goal

Make `NickHugi/PyKotor` redirect to `OldRepublicDevs/PyKotor`, just like `th3w1zard1/PyKotor` was transferred.

## Current Status

- ✅ `th3w1zard1/PyKotor` → Transferred to `OldRepublicDevs/PyKotor` (redirects automatically)
- ❌ `NickHugi/PyKotor` → Still exists separately
- ✅ `OldRepublicDevs/PyKotor` → Source of truth repository

## Required Action

**NickHugi** needs to transfer their repository to the OldRepublicDevs organization.

## Steps for NickHugi

### Option 1: Transfer Repository (Recommended - Creates Automatic Redirect)

1. Go to: <https://github.com/NickHugi/PyKotor/settings>
2. Scroll down to the **"Danger Zone"** section
3. Click **"Transfer ownership"**
4. Enter: `OldRepublicDevs` as the new owner
5. Type the repository name `PyKotor` to confirm
6. Click **"I understand, transfer this repository"**

**Note:** Since `OldRepublicDevs/PyKotor` already exists, GitHub will either:

- Automatically merge/redirect (preferred)
- Or require a temporary name change first

### Option 2: Delete Repository (If Transfer Fails)

If the transfer fails due to name conflict:

1. Go to: <https://github.com/NickHugi/PyKotor/settings>
2. Scroll down to the **"Danger Zone"** section  
3. Click **"Delete this repository"**
4. Type `NickHugi/PyKotor` to confirm
5. Click **"I understand the consequences, delete this repository"**

**After deletion**, GitHub will show a redirect notice pointing to `OldRepublicDevs/PyKotor` if it's set as the canonical source.

## Alternative: Use GitHub CLI (If NickHugi has CLI access)

```bash
# Transfer to organization
gh api repos/NickHugi/PyKotor/transfer -X POST -f new_owner=OldRepublicDevs

# Or delete (if transfer fails)
gh repo delete NickHugi/PyKotor --confirm
```

## What Happens After Transfer/Deletion

- ✅ All URLs to `github.com/NickHugi/PyKotor` will redirect to `github.com/OldRepublicDevs/PyKotor`
- ✅ All git clones using `NickHugi/PyKotor` URLs will continue to work
- ✅ All issues, PRs, and links will redirect automatically
- ✅ The repository history is preserved in `OldRepublicDevs/PyKotor`

## Verification

After the transfer/deletion, verify:

```bash
gh api repos/NickHugi/PyKotor
# Should either show OldRepublicDevs/PyKotor or 404 with redirect
```

## Current Permissions

- **th3w1zard1** (current user): Has push/triage permissions, but NOT admin
- **NickHugi**: Has admin permissions (can transfer/delete)
- **OldRepublicDevs org**: Has admin permissions on OldRepublicDevs/PyKotor

## Important Notes

⚠️ **All content from NickHugi/PyKotor will be gone** - but that's what you want since OldRepublicDevs/PyKotor is the source of truth.

✅ **No data loss** - All important content (tags, releases) has already been migrated to OldRepublicDevs/PyKotor.

✅ **Automatic redirects** - GitHub handles redirects automatically for transferred/deleted repositories.
