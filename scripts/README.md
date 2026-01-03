# Scripts Directory

This directory contains utility scripts for the PyKotor project, organized into subfolders.

## Organization

Scripts are organized into subfolders:

- **`workflow/`** - Scripts related to CI/CD, version management, releases, GitHub workflows, and development setup
- **`kotor/`** - Scripts related to the KOTOR game (resource checks, investigations, debugging, testing)
- **`kotor_re_things/`** - Scripts for integrating KOTOR RE Things reverse engineering data and Ghidra integration
- **Root `scripts/`** - General utility scripts, documentation updates, code generation, and fixes

### `workflow/` - Workflow and Development Scripts

Scripts related to CI/CD, version management, releases, GitHub workflows, and development setup:

- **Version Management:**
  - `bump_version.ps1` - Bump version for PyKotor tools
  - `sync_versions.py` - Synchronize versions across packages

- **Submodule Management:**
  - `create_submodule_repo.ps1` - Create a standalone GitHub repo and configure as submodule
  - `remove_submodule_repo.ps1` - Remove a submodule and convert back to regular directory
  - `create_all_submodule_repos.ps1` - Batch create submodule repos
  - `remove_all_submodule_repos.ps1` - Batch remove submodule repos
  - `update_submodules.ps1` / `update_submodules.sh` - Update all submodules
  - `fork_missing_repos.ps1` - Fork missing repositories

- **CI/CD and Workflows:**
  - `generate_standalone_workflows.ps1` - Generate GitHub Actions workflows
  - `create_workflows.py` - Create workflow files
  - `create_github_labels.py` - Create GitHub labels

- **Releases:**
  - `package_kits.ps1` - Package kits for release
  - `release_kits.ps1` - Release kits

- **Setup:**
  - `setup_dev_environment.ps1` / `setup_dev_environment.sh` - Setup development environment
  - `install_holocrontoolset_from_pypi.ps1` - Install HolocronToolset from PyPI
  - `test_holocrontoolset_install.ps1` - Test HolocronToolset installation

- **Project Configuration:**
  - `update_pyproject_for_uvx.ps1` - Update pyproject.toml for uvx compatibility
  - `update_setup_files.py` - Update setup files

### `kotor/` - KOTOR Game-Related Scripts

Scripts related to the KOTOR game: resource checks, investigations, debugging, and testing:

- **Resource Checks:**
  - `check_txi_files.py` - Check if TXI files exist for textures
  - `check_missing_resources.py` - Check if missing resources are referenced
  - `check_genericdoors.py` - Check if a 2DA file exists
  - `check_genericdoors_row.py` - Check a specific row in genericdoors.2da
  - `check_door_appearance_ids.py` - Check door appearance IDs
  - `check_door_dims.py` - Check door dimensions in kit JSON
  - `check_missing_textures_in_rim.py` - Check if missing textures are in RIM files
  - `check_missing_texture_refs.py` - Check missing texture references

- **Investigation:**
  - `investigate_module_structure.py` - Investigate module structure
  - `investigate_kit_resources.py` - Investigate kit resources

- **Debugging:**
  - `debug_door_dimensions.py` - Debug door dimension extraction
  - `debug_txi_embedded.py` - Debug embedded TXI files
  - `debug_txi_lookup.py` - Debug TXI lookup
  - `debug_bwm_roundtrip.py` - Debug BWM roundtrip
  - `debug_run.py` - Minimal debug script

- **Testing:**
  - `test_indoor_diff.py` - Test Indoor Map Builder module functionality
  - `test_single_door_dimension.py` - Test single door dimension extraction
  - `test_wav_loading.py` - Test WAV file loading

- **Analysis:**
  - `compare_kit_json_files.py` - Compare kit JSON files
  - `compare_kit_json.py` - Compare kit JSON
  - `analyze_generated_json.py` - Analyze generated JSON

### `kotor_re_things/` - KOTOR RE Things and Ghidra Integration

Scripts for integrating KOTOR RE Things reverse engineering data and Ghidra integration:

- **Ghidra Integration:**
  - `apply_ghidra_integration.py` - Apply Ghidra integration
  - `apply_to_ghidra.py` - Apply changes to Ghidra
  - `batch_apply_ghidra.py` - Batch apply Ghidra changes
  - `ghidra_batch_apply.py` - Batch apply Ghidra integration
  - `ghidra_force_analyze.py` - Force Ghidra analysis
  - `ghidra_kotor_apply.py` - Apply KOTOR-specific Ghidra changes
  - `ghidra_kotor_import.py` - Import KOTOR data into Ghidra
  - `ghidra_batches.txt` - Batch configuration file
  - `GHIDRA_INTEGRATION_SUMMARY.md` - Ghidra integration documentation

- **KOTOR RE Things:**
  - `integrate_kotor_re_things.py` - Integrate KOTOR RE Things reverse engineering data
  - `kotor_re_full.json` - Full KOTOR RE Things data
  - `kotor_re_parsed.json` - Parsed KOTOR RE Things data
  - `KOTOR_RE_INTEGRATION_SUMMARY.md` - KOTOR RE Things integration documentation

- **DRM/Unpacking:**
  - `kotor_drm_unpacker.py` - KOTOR DRM unpacker
  - `KOTOR_DRM_README.md` - DRM unpacking documentation

### Root `scripts/` - General Utility Scripts

General utility scripts, documentation updates, code generation, and fixes:

- **Documentation:**
  - `verify_toc.py` - Verify TOC in markdown files
  - `verify_anchors.py` - Verify anchors in markdown files
  - `update_nss_main.py` - Update NSS documentation
  - `update_nss_documentation.py` - Update NSS documentation
  - `update_home_2da_toc.py` - Update 2DA documentation TOC
  - `update_gff_main.py` - Update GFF documentation
  - `update_2da_main.py` - Update 2DA documentation
  - `sort_nss_toc.py` - Sort NSS TOC
  - `sort_2da_toc.py` - Sort 2DA TOC
  - `convert_pdf_to_markdown.py` - Convert PDF to markdown

- **Code Generation:**
  - `generate_scriptdefs.py` - Generate scriptdefs.py from NSS files
  - `generate_dencs_nodes.py` - Generate DeNCS node implementations
  - `parse_nss_to_python.py` - Parse NSS to Python
  - `extract_nss_sections.py` - Extract NSS sections
  - `extract_gff_generics.py` - Extract GFF generics
  - `extract_2da_files.py` - Extract 2DA files
  - `pcode_to_ncs.py` - Convert pcode to NCS

- **Utilities:**
  - `find_localization_strings.py` - Find hardcoded strings needing localization
  - `normalize_pythonpath.py` - Normalize PYTHONPATH
  - `expand_translations.py` - Expand translations
  - `move_markdown_to_docs.py` - Move markdown to docs

- **Fixes:**
  - `fix_all_dencs_imports.py` - Fix all DeNCS imports
  - `fix_dencs_imports.py` - Fix DeNCS imports
  - `fix_empty_type_checking.py` - Fix empty type checking
  - `fix_help_tests.py` - Fix help tests
  - `fix_help_tests_cleanup.py` - Fix help tests cleanup
  - `fix_qss_variables.py` - Fix QSS variables
  - `fix_tpc_ui.py` - Fix TPC UI
  - `remove_debug_prints.py` - Remove debug prints

- **Testing:**
  - `add_help_tests.py` - Add help tests
  - `test_conversion.py` - Test conversion
  - `test_decompile.py` - Test decompilation
  - `test_nwnnsscomp.py` - Test NWN NSS compiler
  - `generate_test_wavs.py` - Generate test WAV files

- **Other:**
  - `add_placeholders.py` - Add placeholders
  - `integrate_vscode_themes.py` - Integrate VS Code themes
  - `nwnnsscomp.py` / `nwnnsscomp_full.py` - NWN NSS compiler
  - `analyze_tokens.py` - Analyze tokens
  - `analyze_profile.py` / `analyze_profile_comprehensive.py` - Analyze profile

## Script Analysis and Refactoring Summary

This section provides a comprehensive analysis of all scripts, categorizing them by reusability and providing recommendations.

## Categories

### ✅ Refactored Scripts (Now Accept Parameters)

These scripts have been refactored to accept command-line arguments and are now reusable:

**KOTOR Scripts (`kotor/`):**

1. **`kotor/check_txi_files.py`** → Accepts `--installation` and `--textures` arguments
2. **`kotor/check_missing_resources.py`** → Accepts `--installation`, `--module`, `--lightmaps`, `--textures`
3. **`kotor/check_genericdoors.py`** → Accepts `--installation` and `--2da` arguments
4. **`kotor/check_door_dims.py`** → Accepts `--file`, `--default-width`, `--default-height`

**General Scripts:**
5. **`verify_toc.py`** → Accepts `--file` argument
6. **`verify_anchors.py`** → Accepts `--file` argument
7. **`find_localization_strings.py`** → Accepts `--directory` argument

### ✅ Keep As-Is (Already Well-Designed)

These scripts already have good parameter handling and don't need refactoring:

**Workflow Scripts (`workflow/`):**

- `workflow/create_submodule_repo.ps1` - Well-designed with parameters
- `workflow/remove_submodule_repo.ps1` - Well-designed with parameters
- `workflow/create_all_submodule_repos.ps1` - Well-designed with parameters
- `workflow/remove_all_submodule_repos.ps1` - Well-designed with parameters
- `workflow/generate_standalone_workflows.ps1` - Well-designed with parameters
- `workflow/update_pyproject_for_uvx.ps1` - Well-designed with parameters
- `workflow/bump_version.ps1` - Well-designed version management
- `workflow/update_submodules.ps1` - Well-designed submodule management
- `workflow/package_kits.ps1` - Well-designed
- `workflow/release_kits.ps1` - Well-designed
- `workflow/setup_dev_environment.ps1` - Well-designed
- `workflow/setup_dev_environment.sh` - Well-designed
- `workflow/sync_versions.py` - Excellent CLI with argparse
- `generate_scriptdefs.py` - Well-designed, uses NSS lexer
- `pcode_to_ncs.py` - Good CLI with argparse
- `test_indoor_diff.py` - Good CLI with argparse
- `convert_pdf_to_markdown.py` - Well-designed utility
- `integrate_vscode_themes.py` - One-time use but well-designed
- `generate_dencs_nodes.py` - Code generation script, well-designed
- `normalize_pythonpath.py` - Utility function, can be imported

### 🔄 Could Be Refactored (Medium Priority)

These scripts could benefit from parameterization but are less critical:

**KOTOR Scripts (`kotor/`):**

1. **`kotor/check_missing_textures_in_rim.py`** - Hardcoded module name and texture list
2. **`kotor/check_genericdoors_row.py`** - Hardcoded row number
3. **`kotor/check_door_appearance_ids.py`** - Hardcoded module name
4. **`kotor/debug_door_dimensions.py`** - Hardcoded module and door
5. **`kotor/test_single_door_dimension.py`** - Hardcoded module and door
6. **`kotor/investigate_module_structure.py`** - Already accepts module name, could add more options
7. **`kotor/investigate_kit_resources.py`** - Hardcoded module and resource lists
8. **`kotor/debug_txi_embedded.py`** - Hardcoded texture list
9. **`kotor/debug_txi_lookup.py`** - Hardcoded texture list
10. **`kotor/compare_kit_json_files.py`** - Hardcoded file paths
11. **`kotor/analyze_generated_json.py`** - Hardcoded file path

### 🗑️ Simple/One-Off Scripts (Candidates for Deletion)

These scripts are very simple, one-time use, or can be easily rewritten:

1. **`test_decompile.py`** - Very simple test script (24 lines), can be rewritten if needed
2. **`kotor/debug_run.py`** - Empty/minimal file (2 bytes)
3. **`remove_debug_prints.py`** - One-time cleanup script (518 bytes)

### 📝 Documentation/Update Scripts (Keep)

These scripts are used for maintaining documentation or code generation:

- `update_nss_main.py` - Updates NSS documentation
- `update_nss_documentation.py` - Updates NSS documentation
- `update_home_2da_toc.py` - Updates 2DA documentation TOC
- `update_gff_main.py` - Updates GFF documentation
- `update_2da_main.py` - Updates 2DA documentation
- `sort_nss_toc.py` - Sorts NSS TOC
- `sort_2da_toc.py` - Sorts 2DA TOC
- `parse_nss_to_python.py` - Code generation
- `extract_nss_sections.py` - Documentation extraction
- `extract_gff_generics.py` - Code generation
- `extract_2da_files.py` - Code generation
- `generate_dencs_nodes.py` - Code generation

### 🧪 Test/Debug Scripts (Keep for Now)

These are useful for debugging specific issues:

**KOTOR Scripts (`kotor/`):**

- `kotor/test_indoor_diff.py` - Comprehensive test suite
- `kotor/test_single_door_dimension.py` - Debug script
- `kotor/test_wav_loading.py` - Test script
- `kotor/debug_bwm_roundtrip.py` - Debug script
- `kotor/debug_door_dimensions.py` - Debug script
- `kotor/debug_txi_embedded.py` - Debug script
- `kotor/debug_txi_lookup.py` - Debug script
- `test_conversion.py` - Test script

### 🔧 Utility Scripts (Keep)

- `add_help_tests.py` - Adds help tests to editor test files
- `fix_help_tests.py` - Fixes help tests
- `fix_help_tests_cleanup.py` - Cleans up help tests
- `fix_all_dencs_imports.py` - Fixes imports
- `fix_dencs_imports.py` - Fixes imports
- `fix_tpc_ui.py` - Fixes TPC UI
- `fix_qss_variables.py` - Fixes QSS variables
- `fix_empty_type_checking.py` - Fixes type checking
- `expand_translations.py` - Expands translations
- `move_markdown_to_docs.py` - Moves markdown files
- `create_github_labels.py` - Creates GitHub labels
- `create_workflows.py` - Creates workflows
- `update_setup_files.py` - Updates setup files
- `add_placeholders.py` - Adds placeholders
- `fork_missing_repos.ps1` - Forks missing repos
- `install_holocrontoolset_from_pypi.ps1` - Installation script
- `test_holocrontoolset_install.ps1` - Test installation

### 📊 Analysis Scripts (Keep)

- `analyze_generated_json.py` - Analyzes generated JSON
- `compare_kit_json.py` - Compares kit JSON files
- `compare_kit_json_files.py` - Compares kit JSON files
- `analyze_tokens.py` - Analyzes tokens
- `analyze_profile.py` - Analyzes profile
- `analyze_profile_comprehensive.py` - Comprehensive profile analysis

### 🔍 Investigation Scripts (Keep)

**KOTOR Scripts (`kotor/`):**

- `kotor/investigate_module_structure.py` - Investigates module structure
- `kotor/investigate_kit_resources.py` - Investigates kit resources
- `kotor/check_missing_resources.py` - Checks missing resources (refactored)
- `kotor/check_missing_textures_in_rim.py` - Checks missing textures
- `kotor/check_missing_texture_refs.py` - Checks missing texture refs

## Recommendations

### High Priority Actions

1. **Delete simple/one-off scripts:**
   - `debug_run.py` (empty file)
   - `test_decompile.py` (very simple, can be rewritten)
   - `remove_debug_prints.py` (one-time cleanup, already done)

2. **Consider refactoring medium-priority scripts** if they're used frequently:
   - `check_missing_textures_in_rim.py`
   - `check_genericdoors_row.py`
   - `compare_kit_json_files.py`

### Medium Priority Actions

1. **Group related scripts** into subdirectories:
   - `debug/` - Debug scripts
   - `test/` - Test scripts
   - `docs/` - Documentation update scripts
   - `generation/` - Code generation scripts

2. **Create shared utility module** for common functions:
   - Installation path resolution
   - Environment variable reading
   - Common argument parsing patterns

### Low Priority Actions

1. **Add docstrings** to all scripts
2. **Standardize error handling** across scripts
3. **Add type hints** where missing

## Usage Examples

### Refactored Scripts

```bash
# KOTOR Scripts (kotor/)
# Check TXI files for specific textures
python scripts/kotor/check_txi_files.py --installation "C:/Games/KOTOR" --textures lda_bark04 lda_flr11

# Check missing resources in a module
python scripts/kotor/check_missing_resources.py --module danm13 --lightmaps m03af_01a_lm13 --textures lda_bark04

# Check if a 2DA file exists
python scripts/kotor/check_genericdoors.py --2da genericdoors --installation "C:/Games/KOTOR"

# Check door dimensions in a kit JSON
python scripts/kotor/check_door_dims.py --file path/to/kit.json --default-width 2.0 --default-height 3.0

# General Scripts
# Verify TOC in a markdown file
python scripts/verify_toc.py --file wiki/NSS-File-Format.md

# Find localization strings in a directory
python scripts/find_localization_strings.py --directory Tools/HolocronToolset/src/toolset

# Workflow Scripts (workflow/)
# Sync versions across packages
python scripts/workflow/sync_versions.py --show

# Bump version for a tool
.\scripts\workflow\bump_version.ps1 -Tool toolset -Version 3.1.3
```

## Notes

- All refactored scripts maintain backward compatibility with default values
- Scripts use environment variables (K1_PATH, K2_PATH) and .env file as fallbacks
- Error handling has been improved in refactored scripts
- All scripts now have proper shebangs and docstrings

## Quick Reference

Most scripts accept command-line arguments. Use `--help` or check the script's docstring for usage information.

### Examples

```bash
# KOTOR Scripts
python scripts/kotor/check_txi_files.py --installation "C:/Games/KOTOR" --textures lda_bark04
python scripts/kotor/check_missing_resources.py --module danm13

# Workflow Scripts
python scripts/workflow/sync_versions.py --show
.\scripts\workflow\bump_version.ps1 -Tool toolset -Version 3.1.3

# General Scripts
python scripts/verify_toc.py --file wiki/NSS-File-Format.md
python scripts/find_localization_strings.py --directory Tools/HolocronToolset/src/toolset
```
