"""PyKotor tools package.

This package contains utility functions for working with KotOR game resources,
including model manipulation, door handling, creature management, and kit generation.
"""

from typing import TYPE_CHECKING

# Lazy import to avoid circular dependency
def __getattr__(name: str):
    if name == "extract_kit":
        from pykotor.tools.kit import extract_kit
        return extract_kit
    if name == "find_module_file":
        from pykotor.tools.kit import find_module_file
        return find_module_file
    if name == "extract_erf":
        from pykotor.tools.archives import extract_erf
        return extract_erf
    if name == "extract_rim":
        from pykotor.tools.archives import extract_rim
        return extract_rim
    if name == "extract_bif":
        from pykotor.tools.archives import extract_bif
        return extract_bif
    if name == "extract_key_bif":
        from pykotor.tools.archives import extract_key_bif
        return extract_key_bif
    if name == "list_erf":
        from pykotor.tools.archives import list_erf
        return list_erf
    if name == "list_rim":
        from pykotor.tools.archives import list_rim
        return list_rim
    if name == "list_bif":
        from pykotor.tools.archives import list_bif
        return list_bif
    if name == "list_key":
        from pykotor.tools.archives import list_key
        return list_key
    if name == "matches_filter":
        from pykotor.tools.archives import matches_filter
        return matches_filter
    if name == "create_erf_from_directory":
        from pykotor.tools.archives import create_erf_from_directory
        return create_erf_from_directory
    if name == "create_rim_from_directory":
        from pykotor.tools.archives import create_rim_from_directory
        return create_rim_from_directory
    if name == "create_key_from_directory":
        from pykotor.tools.archives import create_key_from_directory
        return create_key_from_directory
    if name == "search_in_erf":
        from pykotor.tools.archives import search_in_erf
        return search_in_erf
    if name == "search_in_rim":
        from pykotor.tools.archives import search_in_rim
        return search_in_rim
    if name == "get_resource_from_archive":
        from pykotor.tools.archives import get_resource_from_archive
        return get_resource_from_archive
    # Format conversions
    if name.startswith("convert_"):
        from pykotor.tools import conversions
        return getattr(conversions, name)
    # Script utilities
    if name in ("decompile_ncs_to_nss", "disassemble_ncs", "ncs_to_text"):
        from pykotor.tools import scripts
        return getattr(scripts, name)
    # Resource conversions
    if name.startswith("convert_") and name in (
        "convert_tpc_to_tga",
        "convert_tga_to_tpc",
        "convert_wav_to_clean",
        "convert_clean_to_wav",
        "convert_mdl_to_ascii",
        "convert_ascii_to_mdl",
        "convert_texture_format",
    ):
        from pykotor.tools import resources
        return getattr(resources, name)
    # Utility commands
    if name in ("diff_files", "grep_in_file", "get_file_stats", "validate_file"):
        from pykotor.tools import utilities
        return getattr(utilities, name)
    # Validation functions
    if name in (
        "check_txi_files",
        "check_2da_file",
        "get_module_referenced_resources",
        "check_missing_resources_referenced",
        "investigate_module_structure",
        "validate_installation",
    ):
        from pykotor.tools import validation
        return getattr(validation, name)
    # Patching functions
    if name in (
        "PatchingConfig",
        "patch_nested_gff",
        "recurse_through_list",
        "translate_locstring",
        "convert_gff_game",
        "process_translations",
        "patch_resource",
        "patch_and_save_noncapsule",
        "patch_capsule_file",
        "patch_erf_or_rim",
        "patch_file",
        "patch_folder",
        "patch_install",
        "is_kotor_install_dir",
        "determine_input_path",
    ):
        from pykotor.tools import patching
        return getattr(patching, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

if TYPE_CHECKING:
    # Type stubs for static analysis - these are lazy-loaded at runtime via __getattr__
    from collections.abc import Iterator
    from pathlib import Path
    from typing import List, Optional, Tuple

    from pykotor.extract.installation import Installation
    from pykotor.resource.bioware_archive import ArchiveResource

    def extract_kit(
        installation: Installation,
        module_name: str,
        output_path: Path,
        *,
        kit_id: Optional[str] = None,
        logger: Optional[object] = None,
    ) -> None: ...
    def find_module_file(installation: Installation, module_name: str) -> Optional[Path]: ...
    def extract_erf(
        erf_path: Path,
        output_dir: Path,
        *,
        filter_pattern: Optional[str] = None,
        resource_filter: Optional[object] = None,
    ) -> Iterator[Tuple[ArchiveResource, Path]]: ...
    def extract_rim(
        rim_path: Path,
        output_dir: Path,
        *,
        filter_pattern: Optional[str] = None,
        resource_filter: Optional[object] = None,
    ) -> Iterator[Tuple[ArchiveResource, Path]]: ...
    def extract_bif(
        bif_path: Path,
        output_dir: Path,
        *,
        key_path: Optional[Path] = None,
        filter_pattern: Optional[str] = None,
        resource_filter: Optional[object] = None,
    ) -> Iterator[Tuple[ArchiveResource, Path]]: ...
    def extract_key_bif(
        key_path: Path,
        output_dir: Path,
        *,
        bif_search_dir: Optional[Path] = None,
        filter_pattern: Optional[str] = None,
        resource_filter: Optional[object] = None,
    ) -> Iterator[Tuple[ArchiveResource, Path, Path]]: ...
    def list_erf(erf_path: Path) -> Iterator[ArchiveResource]: ...
    def list_rim(rim_path: Path) -> Iterator[ArchiveResource]: ...
    def list_bif(
        bif_path: Path,
        *,
        key_path: Optional[Path] = None,
    ) -> Iterator[ArchiveResource]: ...
    def list_key(key_path: Path) -> "Tuple[List[str], List[Tuple[str, str, int, int]]]": ...
    def matches_filter(text: str, pattern: str) -> bool: ...
    def create_erf_from_directory(
        input_dir: Path,
        output_path: Path,
        *,
        erf_type: str = "ERF",
        file_filter: Optional[str] = None,
    ) -> None: ...
    def create_rim_from_directory(
        input_dir: Path,
        output_path: Path,
        *,
        file_filter: Optional[str] = None,
    ) -> None: ...
    def create_key_from_directory(
        input_dir: Path,
        bif_dir: Path,
        output_path: Path,
        *,
        file_filter: Optional[str] = None,
    ) -> None: ...
    def search_in_erf(
        erf_path: Path,
        pattern: str,
        *,
        case_sensitive: bool = False,
        search_content: bool = False,
    ) -> Iterator[Tuple[str, str]]: ...
    def search_in_rim(
        rim_path: Path,
        pattern: str,
        *,
        case_sensitive: bool = False,
        search_content: bool = False,
    ) -> Iterator[Tuple[str, str]]: ...
    def get_resource_from_archive(
        archive_path: Path,
        resref: str,
        restype: Optional[str] = None,
    ) -> Optional[bytes]: ...

__all__ = [
    "extract_kit",
    "find_module_file",
    "extract_erf",
    "extract_rim",
    "extract_bif",
    "extract_key_bif",
    "list_erf",
    "list_rim",
    "list_bif",
    "list_key",
    "matches_filter",
    "create_erf_from_directory",
    "create_rim_from_directory",
    "create_key_from_directory",
    "search_in_erf",
    "search_in_rim",
    "get_resource_from_archive",
    # Format conversions (imported from conversions module)
    "convert_gff_to_xml",
    "convert_xml_to_gff",
    "convert_tlk_to_xml",
    "convert_xml_to_tlk",
    "convert_ssf_to_xml",
    "convert_xml_to_ssf",
    "convert_2da_to_csv",
    "convert_csv_to_2da",
    "convert_gff_to_json",
    "convert_json_to_gff",
    "convert_tlk_to_json",
    "convert_json_to_tlk",
    # Script utilities (imported from scripts module)
    "decompile_ncs_to_nss",
    "disassemble_ncs",
    "ncs_to_text",
    # Resource conversions (imported from resources module)
    "convert_tpc_to_tga",
    "convert_tga_to_tpc",
    "convert_wav_to_clean",
    "convert_clean_to_wav",
    "convert_mdl_to_ascii",
    "convert_ascii_to_mdl",
    "convert_texture_format",
    # Utility commands (imported from utilities module)
    "diff_files",
    "grep_in_file",
    "get_file_stats",
    "validate_file",
    # Validation functions (imported from validation module)
    "check_txi_files",
    "check_2da_file",
    "get_module_referenced_resources",
    "check_missing_resources_referenced",
    "investigate_module_structure",
    "validate_installation",
    # Patching functions (imported from patching module)
    "PatchingConfig",
    "patch_nested_gff",
    "recurse_through_list",
    "translate_locstring",
    "convert_gff_game",
    "process_translations",
    "patch_resource",
    "patch_and_save_noncapsule",
    "patch_capsule_file",
    "patch_erf_or_rim",
    "patch_file",
    "patch_folder",
    "patch_install",
    "is_kotor_install_dir",
    "determine_input_path",
]

