# Scripts Directory

This directory contains utility scripts for the PyKotor project, organized into subfolders:

## Organization

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

## Usage

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

## See Also

- `SCRIPT_ANALYSIS.md` - Detailed analysis of all scripts
