"""Validation and investigation utilities for KOTOR installations and modules.

This module provides functions for:
- Checking resource availability (TXI files, 2DA files, etc.)
- Validating module structure
- Investigating resource references
- Checking missing resources

References:
----------
    scripts/kotor/check_txi_files.py - TXI file checking
    scripts/kotor/check_missing_resources.py - Missing resource checking
    scripts/kotor/investigate_module_structure.py - Module investigation
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.module import Module


class ValidationResult(TypedDict):
    """Result of installation validation."""

    valid: bool
    missing_files: list[str]
    errors: list[str]


def check_txi_files(
    installation: Installation,
    texture_names: list[str],
    *,
    search_locations: list[SearchLocation] | None = None,
) -> dict[str, list[Path]]:
    """Check if TXI files exist for given textures.

    Args:
    ----
        installation: KOTOR installation to check
        texture_names: List of texture names to check
        search_locations: Optional list of search locations (default: all common locations)

    Returns:
    -------
        Dictionary mapping texture names to lists of file paths where TXI was found

    Example:
    -------
        >>> inst = Installation("C:/Games/KOTOR")
        >>> results = check_txi_files(inst, ["lda_bark04", "lda_flr11"])
        >>> print(results["lda_bark04"])  # List of paths where TXI was found
    """
    if search_locations is None:
        search_locations = [
            SearchLocation.OVERRIDE,
            SearchLocation.TEXTURES_GUI,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.CHITIN,
        ]

    results: dict[str, list[Path]] = {}

    for tex_name in texture_names:
        locations = installation.locations(
            [ResourceIdentifier(resname=tex_name, restype=ResourceType.TXI)],
            search_locations,
        )
        found_paths: list[Path] = []
        for res_ident, loc_list in locations.items():
            for loc in loc_list:
                if loc.filepath and loc.filepath not in found_paths:
                    found_paths.append(loc.filepath)
        results[tex_name] = found_paths

    return results


def check_2da_file(
    installation: Installation,
    twoda_name: str,
    *,
    search_locations: list[SearchLocation] | None = None,
) -> tuple[bool, list[Path]]:
    """Check if a 2DA file exists in installation.

    Args:
    ----
        installation: KOTOR installation to check
        twoda_name: Name of the 2DA file (without extension)
        search_locations: Optional list of search locations (default: CHITIN, OVERRIDE)

    Returns:
    -------
        Tuple of (found: bool, paths: list[Path])

    Example:
    -------
        >>> inst = Installation("C:/Games/KOTOR")
        >>> found, paths = check_2da_file(inst, "genericdoors")
        >>> if found:
        ...     print(f"Found at: {paths[0]}")
    """
    if search_locations is None:
        search_locations = [SearchLocation.CHITIN, SearchLocation.OVERRIDE]

    locations = installation.locations(
        [ResourceIdentifier(resname=twoda_name, restype=ResourceType.TwoDA)],
        search_locations,
    )

    found_paths: list[Path] = []
    for res_ident, loc_list in locations.items():
        for loc in loc_list:
            if loc.filepath and loc.filepath not in found_paths:
                found_paths.append(loc.filepath)

    return len(found_paths) > 0, found_paths


def get_module_referenced_resources(
    module: Module,
) -> tuple[set[str], set[str]]:
    """Get all textures and lightmaps referenced by a module's models.

    Args:
    ----
        module: Module to analyze

    Returns:
    -------
        Tuple of (textures: set[str], lightmaps: set[str])

    Example:
    -------
        >>> from pykotor.common.module import Module
        >>> module = Module("danm13", installation)
        >>> textures, lightmaps = get_module_referenced_resources(module)
        >>> print(f"Module references {len(textures)} textures and {len(lightmaps)} lightmaps")
    """
    from pykotor.tools.model import iterate_lightmaps, iterate_textures

    all_lightmaps: set[str] = set()
    all_textures: set[str] = set()

    for mdl in module.models():
        try:
            mdl_data = mdl.data()
            if mdl_data is None:
                continue
            for lm in iterate_lightmaps(mdl_data):
                all_lightmaps.add(lm.lower())
            for tex in iterate_textures(mdl_data):
                all_textures.add(tex.lower())
        except Exception:
            continue

    return all_textures, all_lightmaps


def check_missing_resources_referenced(
    module: Module,
    missing_textures: list[str] | None = None,
    missing_lightmaps: list[str] | None = None,
) -> dict[str, bool]:
    """Check if missing resources are actually referenced by module models.

    Args:
    ----
        module: Module to check
        missing_textures: Optional list of texture names to check
        missing_lightmaps: Optional list of lightmap names to check

    Returns:
    -------
        Dictionary mapping resource names to whether they're referenced

    Example:
    -------
        >>> module = Module("danm13", installation)
        >>> results = check_missing_resources_referenced(
        ...     module,
        ...     missing_textures=["lda_bark04", "lda_flr11"],
        ...     missing_lightmaps=["m03af_01a_lm13"]
        ... )
        >>> print(results["lda_bark04"])  # True if referenced, False otherwise
    """
    all_textures, all_lightmaps = get_module_referenced_resources(module)

    results: dict[str, bool] = {}

    if missing_textures:
        for tex in missing_textures:
            results[tex] = tex.lower() in all_textures

    if missing_lightmaps:
        for lm in missing_lightmaps:
            results[lm] = lm.lower() in all_lightmaps

    return results


def investigate_module_structure(
    module: Module,
) -> dict:
    """Investigate a module's structure and return detailed information.

    Args:
    ----
        module: Module to investigate

    Returns:
    -------
        Dictionary containing:
        - rooms: List of room information
        - resources: Resource counts by type
        - textures: Set of texture names
        - lightmaps: Set of lightmap names
        - components: Room component information

    Example:
    -------
        >>> module = Module("danm13", installation)
        >>> info = investigate_module_structure(module)
        >>> print(f"Module has {len(info['rooms'])} rooms")
        >>> print(f"Total resources: {sum(info['resources'].values())}")
    """
    from pykotor.resource.formats.lyt.lyt_auto import read_lyt
    from pykotor.resource.formats.rim import read_rim
    from pykotor.tools.model import iterate_lightmaps, iterate_textures

    installation = module._installation
    module_name = module._root

    # Get RIM files
    rims_path = installation.rims_path()
    modules_path = installation.module_path()

    main_rim_path = rims_path / f"{module_name}.rim" if rims_path.exists() else None
    data_rim_path = rims_path / f"{module_name}_s.rim" if rims_path.exists() else None

    if main_rim_path is None or not main_rim_path.exists():
        main_rim_path = modules_path / f"{module_name}.rim" if modules_path.exists() else None
    if data_rim_path is None or not data_rim_path.exists():
        data_rim_path = modules_path / f"{module_name}_s.rim" if modules_path.exists() else None

    # Read RIM files
    main_rim = read_rim(main_rim_path) if main_rim_path and main_rim_path.exists() else None
    data_rim = read_rim(data_rim_path) if data_rim_path and data_rim_path.exists() else None

    # Collect all resources
    all_resources: dict[tuple[str, ResourceType], bytes] = {}
    if main_rim:
        for resource in main_rim:
            key = (resource.resref.get().lower(), resource.restype)
            if key not in all_resources:
                all_resources[key] = resource.data
    if data_rim:
        for resource in data_rim:
            key = (resource.resref.get().lower(), resource.restype)
            if key not in all_resources:
                all_resources[key] = resource.data

    # Find LYT file
    lyt_data = None
    lyt_resname = None
    for (resname, restype), data in all_resources.items():
        if restype == ResourceType.LYT:
            lyt_data = data
            lyt_resname = resname
            break

    rooms: list[dict] = []
    room_components: dict[str, dict] = {}

    if lyt_data:
        lyt = read_lyt(lyt_data)
        for room in lyt.rooms:
            model_name = room.model.lower()
            rooms.append({
                "model": model_name,
                "position": (room.position.x, room.position.y, room.position.z),
            })

            # Check for MDL/MDX/WOK
            mdl_key = (model_name, ResourceType.MDL)
            mdx_key = (model_name, ResourceType.MDX)
            wok_key = (model_name, ResourceType.WOK)

            textures: set[str] = set()
            lightmaps: set[str] = set()

            if mdl_key in all_resources:
                mdl_data = all_resources[mdl_key]
                textures.update(iterate_textures(mdl_data))
                lightmaps.update(iterate_lightmaps(mdl_data))

            room_components[model_name] = {
                "has_mdl": mdl_key in all_resources,
                "has_mdx": mdx_key in all_resources,
                "has_wok": wok_key in all_resources,
                "textures": list(textures),
                "lightmaps": list(lightmaps),
            }

    # Count resources by type
    resource_counts: dict[str, int] = {}
    for (resname, restype), _ in all_resources.items():
        type_name = restype.extension
        resource_counts[type_name] = resource_counts.get(type_name, 0) + 1

    # Get all textures and lightmaps from module
    module_textures, module_lightmaps = get_module_referenced_resources(module)

    return {
        "module_name": module_name,
        "main_rim": str(main_rim_path) if main_rim_path else None,
        "data_rim": str(data_rim_path) if data_rim_path else None,
        "total_resources": len(all_resources),
        "resources_by_type": resource_counts,
        "lyt_file": lyt_resname,
        "rooms": rooms,
        "room_components": room_components,
        "textures": list(module_textures),
        "lightmaps": list(module_lightmaps),
    }


def validate_installation(
    installation: Installation,
    *,
    check_essential_files: bool = True,
) -> ValidationResult:
    """Validate a KOTOR installation.

    Args:
    ----
        installation: Installation to validate
        check_essential_files: Whether to check for essential game files

    Returns:
    -------
        Dictionary with validation results:
        - valid: bool - Whether installation is valid
        - missing_files: list[str] - List of missing essential files
        - errors: list[str] - List of validation errors

    Example:
    -------
        >>> inst = Installation("C:/Games/KOTOR")
        >>> results = validate_installation(inst)
        >>> if not results["valid"]:
        ...     print(f"Missing files: {results['missing_files']}")
    """
    errors: list[str] = []
    missing_files: list[str] = []

    # Check installation path exists
    install_path = Path(installation.path())
    if not install_path.exists():
        errors.append(f"Installation path does not exist: {install_path}")

    # Check essential files if requested
    if check_essential_files:
        essential_2das = ["appearance", "baseitems", "classes", "genericdoors"]
        for twoda_name in essential_2das:
            found, _ = check_2da_file(installation, twoda_name)
            if not found:
                missing_files.append(f"{twoda_name}.2da")

    valid = len(errors) == 0 and len(missing_files) == 0

    return {
        "valid": valid,
        "missing_files": missing_files,
        "errors": errors,
    }

