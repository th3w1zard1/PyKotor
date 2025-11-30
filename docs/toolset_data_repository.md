# ToolsetData Repository Structure

## Overview

The `th3w1zard1/ToolsetData` repository serves as a centralized storage and distribution system for HolocronToolset data assets, particularly the Indoor Map Builder kits. This separation from the main PyKotor repository allows for:

- Independent versioning of data assets
- Reduced main repository size
- More frequent kit updates without full toolset releases
- Better bandwidth management for users
- Cleaner CI/CD workflows

## Repository Structure

```
th3w1zard1/ToolsetData/
├── .github/
│   └── workflows/
│       └── release-kits.yml          # Automated release workflow
├── kits/                              # Kit source directory
│   ├── blackvulkar/                   # Black Vulkar Base kit
│   │   ├── textures/                  # Kit textures (.tga files)
│   │   ├── lightmaps/                 # Kit lightmaps (.tga files)
│   │   ├── skyboxes/                  # Skybox models (.mdl/.mdx)
│   │   ├── doorway/                   # Doorway padding models
│   │   ├── always/                    # Always-included resources
│   │   ├── *.mdl                      # Component models
│   │   ├── *.mdx                      # Component model extensions
│   │   ├── *.wok                      # Walkmesh files
│   │   ├── *.png                      # Component preview images
│   │   └── *.utd                      # Door templates
│   ├── endarspire/                    # Endar Spire kit
│   ├── hiddenbek/                     # Hidden Bek Base kit
│   ├── blackvulkar.json               # Kit metadata
│   ├── endarspire.json                # Kit metadata
│   └── hiddenbek.json                 # Kit metadata
├── scripts/
│   └── package_kits.ps1               # Packaging script
└── README.md
```

## Kit Structure

Each kit consists of:

### 1. Kit Metadata JSON (`{kit_id}.json`)

Located in the root `kits/` directory, defines the kit structure:

```json
{
    "name": "Black Vulkar Base",
    "id": "blackvulkar",
    "version": 1,
    "doors": [
        {
            "utd_k1": "door01",
            "utd_k2": "door01",
            "width": 2,
            "height": 3
        }
    ],
    "components": [
        {
            "name": "Hallway 01",
            "id": "bv_hall01",
            "doorhooks": [
                {
                    "x": 0.0,
                    "y": 5.0,
                    "z": 0.0,
                    "rotation": 0,
                    "door": 0,
                    "edge": "north"
                }
            ]
        }
    ]
}
```

### 2. Kit Assets Directory (`{kit_id}/`)

Contains all kit resources:

- **textures/** - Wall, floor, and environmental textures
- **lightmaps/** - Pre-baked lighting information
- **skyboxes/** - Sky dome models for outdoor/window views
- **doorway/** - Padding models for door frames
- **always/** - Resources included in every module built with this kit
- **Component files** - Models, walkmeshes, previews for each room component

## Release Process

### Automated (Recommended)

1. Update kit files in the `kits/` directory
2. Commit and push changes
3. Run the GitHub Actions workflow or use the release script
4. The workflow automatically:
   - Validates kit structure
   - Packages all kits into `kits.zip`
   - Creates a GitHub release
   - Uploads the asset

### Manual Process

Using the provided PowerShell script from PyKotor repository:

```powershell
# From PyKotor root directory
cd scripts
.\release_kits.ps1
```

Options:
- `-tag "v1.0.0"` - Specify release tag
- `-draft` - Create as draft release
- `-prerelease` - Mark as pre-release
- `-force` - Recreate if exists
- `-repo "owner/repo"` - Target different repository

Example:
```powershell
.\release_kits.ps1 -tag "v1.0.0" -draft
```

## Integration with HolocronToolset

### Download Configuration

The toolset's `config.py` specifies the download source:

```python
"kits": {
    "Black Vulkar Base": {"version": 1, "id": "blackvulkar"},
    "Endar Spire": {"version": 1, "id": "endarspire"},
    "Hidden Bek Base": {"version": 1, "id": "hiddenbek"},
    "repository": "th3w1zard1/ToolsetData",
    "release_tag": "latest",
}
```

### Download Workflow

1. User opens Indoor Map Builder
2. If kits missing, prompted to open Kit Downloader
3. Kit Downloader:
   - Fetches release info from GitHub API
   - Shows individual kit buttons and "Download All" button
   - Downloads `kits.zip` from specified release
   - Extracts to local `kits/` directory
   - Validates kit structure

### Version Management

Kit versions are tracked in both:
- **Remote**: Kit JSON `version` field in ToolsetData
- **Local**: Kit JSON `version` field in user's installation

The toolset compares versions and shows "Update Available" when remote is newer.

## Best Practices

### For Kit Developers

1. **Increment versions** - Always bump version number when updating kits
2. **Test locally** - Verify kits load correctly in Indoor Map Builder
3. **Validate structure** - Ensure all required files exist
4. **Document changes** - Update release notes for significant changes
5. **Optimize assets** - Compress textures appropriately
6. **Maintain compatibility** - Ensure backward compatibility when possible

### For Repository Maintainers

1. **Tag semantically** - Use semantic versioning (v1.0.0, v1.1.0, etc.)
2. **Keep releases clean** - Delete outdated releases if needed
3. **Monitor size** - Keep kits.zip under 100MB for reasonable download times
4. **Validate PRs** - Run validation scripts before merging kit updates
5. **Update docs** - Keep this documentation current

## Troubleshooting

### Kit Download Fails

- Verify `th3w1zard1/ToolsetData` repository exists and is public
- Check if release with specified tag exists
- Ensure `kits.zip` asset is attached to release
- Verify GitHub API rate limits not exceeded

### Kit Doesn't Load

- Check kit JSON structure matches expected format
- Verify all referenced files exist in kit directory
- Ensure file paths use correct case (case-sensitive on some systems)
- Check for corrupted model or texture files

### Version Mismatch

- Update config.py versions to match ToolsetData releases
- Increment kit versions when making changes
- Clear local kits cache if seeing stale data

## Migration from Old System

The old system downloaded from:
- `NickHugi/PyKotor` repository
- Branch: `master`
- Path: `Tools/HolocronToolset/downloads/kits.zip`

The new system downloads from:
- `th3w1zard1/ToolsetData` repository
- GitHub Releases (tag: `latest` or specific version)
- Asset: `kits.zip`

### Migration Benefits

1. **Efficiency** - Single download for all kits vs. repeated downloads
2. **Versioning** - Proper semantic versioning via releases
3. **Size** - Reduced main repository size
4. **Speed** - Faster updates without full repo clone
5. **Reliability** - Release assets have better availability

## Future Enhancements

Potential improvements to the system:

1. **Individual kit downloads** - Allow downloading single kits from releases
2. **Kit marketplace** - Community-contributed kits
3. **Automatic updates** - Background kit updates
4. **Differential updates** - Only download changed files
5. **CDN integration** - Faster worldwide distribution
6. **Checksum verification** - Ensure download integrity

## References

- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [HolocronToolset Indoor Map Builder](./tools/indoor_map_builder.md)
- [Kit Development Guide](./development/kit_development.md)

