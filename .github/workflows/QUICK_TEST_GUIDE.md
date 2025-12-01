# Quick Test Guide

## Testing Releases Before Production

This guide shows you how to test the release system without affecting production.

## Method 1: PR Build Validation (Recommended)

The easiest way to test that your changes will build correctly:

1. **Create a PR** with your changes (even just a version bump)
2. **Wait for PR Build Validation** workflow to run
3. **Check results** - the workflow will:
   - Detect which tools are affected
   - Run dry-run builds (validates everything without full compile)
   - Post a summary comment on your PR

```bash
# Example: Create a branch to test toolset build
git checkout -b test-toolset-build
# Make any change to toolset files, or just bump version
git commit --allow-empty -m "test: trigger build validation"
git push origin test-toolset-build
# Create PR via GitHub UI
```

## Method 2: Release Readiness Check

For more thorough pre-release testing:

1. Go to **Actions** → **Release Readiness Check**
2. Click **Run workflow**
3. Fill in:
   - **Tool**: Select the tool (e.g., `toolset`)
   - **Version**: Enter the version to test (e.g., `3.1.3`)
   - **Run full builds**: Enable for complete testing
4. Review the results in the workflow summary

### What Gets Tested

- ✅ Version format validation
- ✅ Tag availability check
- ✅ Config file validation
- ✅ Dependency installation
- ✅ Compile script verification
- ✅ Dry-run or full builds

## Method 3: Test Release Workflow

For testing the actual release automation:

### Quick Commands

```bash
# Create test release (uses test-release branch, never touches master)
git tag test-v3.1.99-toolset
git push origin test-v3.1.99-toolset
gh release create test-v3.1.99-toolset --prerelease --title "TEST" --notes "Testing release workflow"

# Wait for TEST_release_toolset.yml to run...
# Check the Actions tab for results

# Cleanup after testing
gh release delete test-v3.1.99-toolset --yes
git push origin --delete test-v3.1.99-toolset
git push origin --delete test-release  # Optional: delete test branch
```

### Key Differences from Production

| Aspect | Production | Test |
|--------|------------|------|
| Tag pattern | `v3.1.3-toolset` | `test-v3.1.3-toolset` |
| Branch modified | `master` | `test-release` |
| Auto-update triggered | ✅ Yes | ❌ No |
| Converts to full release | ✅ Yes | ❌ No (stays pre-release) |
| Artifact retention | 90 days | 7 days |

## Method 4: Fork Testing

For complete end-to-end testing:

1. Fork the repository
2. Enable Actions on your fork
3. Create a real release (e.g., `v99.0.0-toolset`)
4. Watch the full workflow run
5. Delete the fork when done

## Workflow Comparison

| What You Want to Test | Use This |
|----------------------|----------|
| Will my changes compile? | PR Build Validation |
| Is everything ready for release? | Release Readiness Check |
| Does the release automation work? | Test Release Workflow |
| Complete production simulation | Fork Testing |

## Common Test Scenarios

### Scenario 1: Testing a Bug Fix

```bash
# 1. Create PR with fix
git checkout -b fix-some-bug
# ... make changes ...
git push origin fix-some-bug
# Create PR - build validation runs automatically

# 2. If build validation passes, merge PR

# 3. Run Release Readiness Check to prepare for release
```

### Scenario 2: Testing Version Bump

```powershell
# Use the helper script in dry-run mode
.\scripts\bump_version.ps1 -Tool toolset -Version 3.1.3 -DryRun

# If happy, actually bump it
.\scripts\bump_version.ps1 -Tool toolset -Version 3.1.3

# Create a PR to trigger build validation
git checkout -b bump-toolset-313
git add Tools/HolocronToolset/src/toolset/config/config_info.py
git commit -m "chore(toolset): bump version to 3.1.3"
git push origin bump-toolset-313
# Create PR and wait for validation
```

### Scenario 3: Testing Build Infrastructure Changes

```bash
# 1. Make changes to compile scripts or workflows
git checkout -b update-build-scripts
# ... make changes to compile/*.ps1 or .github/workflows/* ...

# 2. Push and create PR
git push origin update-build-scripts
# Build validation will test ALL tools since compile/ changed

# 3. For full builds, run Release Readiness Check with "Run full builds" enabled
```

## Troubleshooting

### Build validation doesn't trigger

- Check if your PR touches the right paths:
  - `Tools/<ToolName>/**`
  - `Libraries/**`
  - `compile/**`
- Workflow only runs on PRs to `main` or `develop`

### Test release workflow doesn't run

- Ensure tag starts with `test-` (e.g., `test-v3.1.3-toolset`)
- Ensure you created a **pre-release** (not full release)
- Check Actions tab for workflow runs

### Full builds fail but dry-run passes

- Dry-run only validates configuration, not actual compilation
- Check PyInstaller logs for the specific error
- Common issues: missing DLLs, spec file errors, resource paths

## Tips

1. **Start with dry-run**: Always test with dry-run first before full builds
2. **Use meaningful test versions**: e.g., `test-v99.0.0-toolset` won't conflict with real versions
3. **Clean up after testing**: Delete test tags, releases, and branches
4. **Check workflow logs**: The Actions tab has detailed logs for debugging
5. **Test on Windows first**: Most users are on Windows, and it has the most complex build

## Quick Reference

```bash
# Validate before merge (automatic)
# Just create a PR!

# Test release readiness (manual)
# Go to Actions → Release Readiness Check → Run workflow

# Test release workflow
git tag test-v99.0.0-toolset
git push origin test-v99.0.0-toolset
gh release create test-v99.0.0-toolset --prerelease --title "TEST" --notes "Test"

# Cleanup test release
gh release delete test-v99.0.0-toolset --yes
git push origin --delete test-v99.0.0-toolset
```
