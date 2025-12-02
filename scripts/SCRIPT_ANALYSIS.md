# Script Analysis and Refactoring Summary

This document provides a comprehensive analysis of all scripts in the `scripts/` folder, categorizing them by reusability and providing recommendations.

## Organization

Scripts are organized into subfolders:

- **`workflow/`** - Scripts related to CI/CD, version management, releases, GitHub workflows, and development setup
- **`kotor/`** - Scripts related to the KOTOR game (resource checks, investigations, debugging, testing)
- **Root `scripts/`** - General utility scripts, documentation updates, code generation, and fixes

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
