# PyPI Auto-Publish Workflow

## Overview

The `publish-pypi-auto.yml` workflow automatically publishes packages to PyPI when:

1. Code is pushed to the **default branch** (determined dynamically, not hardcoded), OR
2. Manually triggered on **any branch or tag**
3. The version in `pyproject.toml` is **greater than** what's currently available on PyPI

This workflow is **completely separate** from release workflows that create `.exe` files and GitHub releases.

## How It Works

### Discovery Phase

The workflow:

1. Scans all first-level subdirectories in `./Libraries` and `./Tools`
2. Finds directories containing `pyproject.toml` files
3. Extracts package name and version from each `pyproject.toml`
4. Queries PyPI API to get the latest published version
5. Compares local version with PyPI version using semantic versioning

### Publishing Decision

A package is published if:

- ✅ Local version > PyPI version (packaging.version comparison)
- ✅ Package doesn't exist on PyPI yet (no published versions found)

A package is **NOT** published if:

- ❌ Local version ≤ PyPI version (already published or downgrade)
- ❌ Workflow is triggered by push to non-default branch (manual runs work on any branch/tag)
- ❌ `pyproject.toml` is missing or malformed
- ❌ Version parsing fails

### Default Branch Detection

The workflow dynamically determines the default branch using the GitHub API:

- No hardcoded branch names (`main` or `master`)
- Works regardless of repository default branch
- For **push events**: Only runs when push is to the actual default branch
- For **manual dispatch**: Runs on any branch or tag specified when triggering

## Version Comparison

The workflow uses Python's `packaging.version` module for semantic version comparison:

- Supports all PEP 440 version formats
- Handles pre-release versions correctly (e.g., `4.0.0a1`, `4.0.0b2`, `4.0.0rc3`)
- Correctly orders versions: `4.0.0a1 < 4.0.0a2 < 4.0.0b1 < 4.0.0`

### Example Scenarios

| Local Version | PyPI Version | Action |
|---------------|--------------|--------|
| `2.0.1` | `2.0.0` | ✅ Publish (newer) |
| `2.0.0` | `2.0.0` | ❌ Skip (same) |
| `2.0.0` | `2.0.1` | ❌ Skip (older) |
| `4.0.0a7` | `4.0.0a6` | ✅ Publish (newer alpha) |
| `4.0.0a1` | `4.0.0` | ❌ Skip (pre-release < release) |
| `1.0.0` | None | ✅ Publish (new package) |

## Workflow Steps

1. **check-default-branch**: Determines repository default branch and validates current push
2. **discover-packages**: Scans directories, compares versions, creates matrix of packages to publish
3. **build-packages**: Builds all packages that need publishing (parallel matrix job)
4. **publish-packages**: Publishes built packages to PyPI using trusted publishing
5. **summary**: Generates summary with list of published packages

## Edge Cases Handled

### Missing Packages

- If a package doesn't exist on PyPI, it's considered for publishing
- First publish of any package is automatic

### Version Format Errors

- Invalid version strings in `pyproject.toml` cause that package to be skipped
- Error is logged but doesn't fail the workflow
- Other valid packages still get published

### PyPI API Failures

- If PyPI API is unreachable, packages are skipped (safe failure)
- Errors are logged but workflow continues
- Prevents publishing if version comparison can't be done

### Concurrent Runs

- Uses concurrency group to prevent multiple simultaneous publishes
- Does NOT cancel in-progress runs (allows previous publish to finish)
- Prevents race conditions on same package

### Build Failures

- Uses `fail-fast: false` in build matrix
- Other packages continue publishing if one fails
- Failed packages are clearly marked in summary

## Configuration

### Required Permissions

```yaml
permissions:
  contents: read      # Read repository contents
  id-token: write     # PyPI trusted publishing (OIDC)
```

### Environment

The workflow uses the `pypi` environment for trusted publishing. Ensure:

- PyPI trusted publishing is configured in repository settings
- OIDC is enabled for GitHub Actions
- Environment secrets are not required (uses OIDC instead)

## Manual Execution

The workflow can be manually triggered on **any branch or tag**:

1. Go to **Actions** → **Auto-Publish to PyPI**
2. Click **Run workflow**
3. Select the branch or tag you want to publish from
4. The workflow will discover and publish packages with newer versions

This is useful for:

- Testing publishing from feature branches
- Publishing from tags/releases
- Emergency publishes
- Publishing packages that were missed by automatic runs

## Integration with Release Workflows

This workflow is **separate** from:

- `release_toolset.yml` - Creates .exe binaries and GitHub releases
- `release_holopatcher.yml` - Creates .exe binaries and GitHub releases
- `release_kotordiff.yml` - Creates .exe binaries and GitHub releases
- `release_guiconverter.yml` - Creates .exe binaries and GitHub releases
- All other `release_*.yml` workflows - Create .exe binaries and GitHub releases (no PyPI publishing)

Release workflows do **NOT** publish to PyPI. Only this auto-publish workflow handles PyPI publishing.

## Monitoring

### Workflow Summary

After each run, check the workflow summary for:

- List of packages that were published
- Previous PyPI versions vs new versions
- Packages that were skipped (with reasons)

### Workflow Logs

Detailed logs show:

- Default branch detection
- Package discovery process
- Version comparison results
- Build and publish status per package

## Troubleshooting

### Workflow Doesn't Run

**Check:**

- Is the push to the default branch? (check `check-default-branch` job output)
- Is the workflow file in the default branch?
- Are GitHub Actions enabled for the repository?

### Package Not Published

**Check:**

- Is version in `pyproject.toml` actually greater than PyPI?
- Is `pyproject.toml` properly formatted with valid version?
- Check `discover-packages` job logs for that specific package

### Build Fails

**Check:**

- Are all dependencies specified in `pyproject.toml`?
- Does the package build successfully locally?
- Check build logs for specific errors

### Publish Fails

**Check:**

- Is PyPI trusted publishing configured correctly?
- Check `publish-packages` job logs for authentication errors
- Ensure OIDC is enabled in repository settings

## Best Practices

1. **Version Bumping**: Update version in `pyproject.toml` before pushing to default branch
2. **Testing**: Test builds locally before pushing to trigger auto-publish
3. **Monitoring**: Check workflow summary after each push to verify expected behavior
4. **Pre-releases**: Pre-release versions (alpha, beta, rc) are compared correctly and will publish if newer

## Example Workflow Run

```
1. Push to default branch (e.g., main)
2. Workflow detects default branch: main ✓
3. Discovers packages:
   - pykotor: 2.0.1 (PyPI: 2.0.0) → Publish ✓
   - pykotorgl: 2.0.0 (PyPI: 2.0.0) → Skip
   - holocrontoolset: 4.0.0a7 (PyPI: 4.0.0a6) → Publish ✓
4. Builds pykotor and holocrontoolset
5. Publishes both to PyPI
6. Summary shows published packages
```
