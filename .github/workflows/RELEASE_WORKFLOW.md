# Automated Release Workflow

## Overview

PyKotor uses an industry-standard CI/CD pipeline for releases. The workflow is designed to **catch issues early** through PR validation, provide **pre-release testing**, and ensure **smooth production releases**.

## The Release Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT PHASE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Create PR with your changes                                             │
│  2. PR Build Validation runs automatically                                  │
│     - Detects which tools are affected                                      │
│     - Validates version config files                                        │
│     - Runs dry-run builds to catch compile issues                          │
│  3. Fix any issues, iterate until PR checks pass                           │
│  4. Merge PR when ready                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PRE-RELEASE VALIDATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  5. Run "Release Readiness Check" workflow (optional but recommended)       │
│     - Validates version format                                              │
│     - Checks tag availability                                               │
│     - Validates dependencies                                                │
│     - Runs dry-run or full builds                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RELEASE PHASE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  6. Bump version in config/config_info.py (use bump_version.ps1 helper)     │
│  7. Commit and push to master                                               │
│  8. Create pre-release on GitHub with proper tag                            │
│  9. Release workflow runs automatically                                     │
│     - Builds all platform binaries                                          │
│     - Uploads to release                                                    │
│     - Updates latest version in config                                      │
│     - Converts to full release                                              │
│ 10. Go to bed happy! 🎉                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Supported Tools

| Tool | Tag Pattern | Config File | Version Key |
|------|-------------|-------------|-------------|
| **HolocronToolset** | `v3.1.3-toolset` | `Tools/HolocronToolset/src/toolset/config/config_info.py` | `currentVersion` |
| **HoloPatcher** | `v1.8.0-patcher` | `Tools/HoloPatcher/src/holopatcher/config.py` | `currentVersion` |
| **KotorDiff** | `v1.0.1-kotordiff` | `Tools/KotorDiff/src/kotordiff/__main__.py` | `CURRENT_VERSION` |
| **GuiConverter** | `v1.0.0-guiconverter` | `Tools/GuiConverter/src/gui_converter/__init__.py` | `__version__` |

## Quick Start: Release a New Version

### Option 1: Using the Helper Script (Recommended)

```powershell
# Preview what will change
.\scripts\bump_version.ps1 -Tool toolset -Version 3.1.3 -DryRun

# Bump version, commit, and create release in one command
.\scripts\bump_version.ps1 -Tool toolset -Version 3.1.3 -Commit -CreateRelease
```

### Option 2: Manual Process

1. **Update version in config file:**

   ```python
   # Tools/HolocronToolset/src/toolset/config/config_info.py
   LOCAL_PROGRAM_INFO: dict[str, Any] = {
       "currentVersion": "3.1.3",  # ← Update this
       ...
   }
   ```

2. **Commit and push:**

   ```bash
   git add Tools/HolocronToolset/src/toolset/config/config_info.py
   git commit -m "chore(toolset): bump version to 3.1.3"
   git push origin master
   ```

3. **Create pre-release on GitHub:**
   - Go to [Releases](https://github.com/th3w1zard1/PyKotor/releases/new)
   - Tag: `v3.1.3-toolset`
   - Title: `toolset v3.1.3`
   - Check "Set as a pre-release"
   - Publish

4. **Wait for automation** - the workflow handles everything else!

## PR Build Validation

When you create a PR that touches tool files, the **PR Build Validation** workflow runs automatically:

### What It Checks

1. **Change Detection**: Identifies which tools are affected by your PR
2. **Version Consistency**: Validates that version config files are properly formatted
3. **Dry-Run Builds**: Validates that the tool can be built (imports work, dependencies install, PyInstaller config valid)

### Trigger Paths

The workflow triggers on changes to:

- `Tools/HolocronToolset/**` → Tests toolset
- `Tools/HoloPatcher/**` → Tests holopatcher
- `Tools/KotorDiff/**` → Tests kotordiff
- `Libraries/**` → Tests ALL tools (shared code)
- `compile/**` → Tests ALL tools (build scripts)

### What Happens

1. **Dry-run builds** validate that builds will succeed:
   - Python environment setup
   - Dependency installation
   - Import validation
   - PyInstaller configuration check

2. **Summary comment** posted to PR with results

3. **Must pass** before merge (recommended to set as required check)

## Release Readiness Check

Run this workflow before releasing to validate everything is ready:

1. Go to **Actions** → **Release Readiness Check**
2. Click **Run workflow**
3. Select tool and enter version
4. Optionally enable full builds

### What It Validates

- ✅ Version format (semver)
- ✅ Tag availability
- ✅ Config file exists and is valid
- ✅ Dependencies can be installed
- ✅ Compile scripts exist
- ✅ Builds succeed (dry-run or full)

## Workflow Architecture

### Reusable Components

```
.github/
├── actions/
│   └── build-tool/           # Reusable build action
│       └── action.yml
└── workflows/
    ├── build-pr.yml          # PR validation (automatic)
    ├── release-ready.yml     # Pre-release checks (manual)
    ├── release_toolset.yml   # Production release
    ├── release_holopatcher.yml
    ├── release_kotordiff.yml
    └── TEST_release_toolset.yml  # Test workflow
```

### Build Action

The `.github/actions/build-tool` action is reusable across all workflows:

```yaml
- uses: ./.github/actions/build-tool
  with:
    tool_name: toolset
    python_version: '3.8'
    architecture: x64
    qt_version: 'PyQt5'
    dry_run: 'true'  # Set to 'false' for full build
```

## Testing Releases Safely

### Option 1: Test Workflow

Use the `TEST_release_toolset.yml` workflow:

1. Create tag: `test-v3.1.99-toolset`
2. Create pre-release with that tag
3. Workflow runs against `test-release` branch
4. **Does NOT modify master**
5. Cleanup when done:

   ```bash
   gh release delete test-v3.1.99-toolset --yes
   git push origin --delete test-v3.1.99-toolset
   ```

### Option 2: Release Readiness with Full Build

1. Run **Release Readiness Check** workflow
2. Enable "Run full builds for all platforms"
3. All artifacts uploaded to workflow run (not a release)
4. Download and test binaries manually

## Troubleshooting

### PR Build Fails

1. Check the **Actions** tab for detailed logs
2. Common issues:
   - Import errors → Check dependencies in `requirements.txt`
   - PyInstaller errors → Check spec file or `compile/` scripts
   - Missing files → Check paths in your changes

### Release Workflow Fails

1. Check if the tag matches the pattern (e.g., `*toolset*` for toolset)
2. Verify pre-release was created (not full release)
3. Check workflow logs for specific errors
4. If upload fails, workflow attempts fallback upload

### Version Not Updating

1. Verify config file path is correct
2. Check that `sed` patterns match your file format
3. Verify workflow has write permissions

## Best Practices

1. **Always test via PR first** - Create a PR even for version bumps
2. **Use semver** - `MAJOR.MINOR.PATCH` format
3. **Run Release Readiness** before production releases
4. **Monitor Actions tab** - Watch the workflow run
5. **Don't skip pre-release** - The automation depends on it

## Version Update Strategy

The release workflow uses a **two-stage update**:

### Stage 1: Pre-Build

- Updates `currentVersion` (what the binary reports)
- Commits to master
- Tags point to this commit
- **Purpose**: Built binaries have correct version

### Stage 2: Post-Upload

- Updates `toolsetLatestVersion` and `toolsetLatestBetaVersion`
- Updates release notes in config
- Commits to master
- Tags updated again
- **Purpose**: Enables auto-update for users

## Migration from Old Workflow

| Old Manual Step | New Automated Step |
|-----------------|-------------------|
| Manually bump currentVersion | Use `bump_version.ps1` or edit config |
| Hope the build works | PR Build Validation catches issues |
| Create release branch | Not needed |
| Wait and pray | Release Readiness Check validates first |
| Manually bump latestVersion | Finalize job does this |
| Convert to full release | Automatic |

## Workflow Files Reference

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-pr.yml` | PR changes | Validates builds before merge |
| `release-ready.yml` | Manual | Pre-release validation |
| `release_toolset.yml` | Pre-release with `*toolset*` tag | Production toolset release |
| `release_holopatcher.yml` | Pre-release with `*patcher*` tag | Production HoloPatcher release |
| `release_kotordiff.yml` | Pre-release with `*kotordiff*` tag | Production KotorDiff release |
| `TEST_release_toolset.yml` | Pre-release with `test-*toolset*` tag | Safe testing |

## Example Timeline

```
Day 1, 10:00 AM  - Create PR with toolset changes
Day 1, 10:02 AM  - PR Build Validation starts
Day 1, 10:10 AM  - ✅ Dry-run builds pass, PR approved
Day 1, 10:15 AM  - Merge PR to master

Day 2, 09:00 AM  - Run Release Readiness Check for v3.1.3
Day 2, 09:05 AM  - ✅ All checks pass

Day 2, 09:10 AM  - Run: .\scripts\bump_version.ps1 -Tool toolset -Version 3.1.3 -Commit -CreateRelease
Day 2, 09:11 AM  - Pre-release created automatically
Day 2, 09:12 AM  - Release workflow starts
Day 2, 09:30 AM  - ✅ All builds complete, artifacts uploaded
Day 2, 09:31 AM  - ✅ Config updated, release finalized
Day 2, 09:32 AM  - 🎉 Go to bed happy!
```
