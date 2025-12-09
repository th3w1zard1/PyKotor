"""Kit generation utilities for extracting kit resources from module RIM files.

This module provides functionality to extract kit resources (MDL, MDX, WOK, TGA, TXI, UTD files)
from module RIM files and generate a kit structure that can be used by the Holocron Toolset.

References:
----------
    Tools/HolocronToolset/src/toolset/data/indoorkit.py - Kit structure
    Tools/HolocronToolset/src/toolset/data/indoormap.py - Indoor map generation
    Libraries/PyKotor/src/pykotor/resource/formats/rim/rim_data.py - RIM file format
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import re

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from pykotor.extract.file import LocationResult
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.bwm import BWM, BWMEdge, BWMFace
    from pykotor.resource.formats.erf import ERF
    from pykotor.resource.formats.rim import RIM

from pykotor.common.module import Module
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import bytes_bwm, read_bwm
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.formats.tpc import read_tpc, write_tpc
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import door as door_tools
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from utility.common.geometry import Vector2, Vector3

# Qt imports for minimap generation
# Set offscreen mode by default to avoid display issues in headless environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QT_AVAILABLE = False
try:
    from qtpy.QtGui import QColor, QImage, QPainter, QPainterPath
    QT_AVAILABLE = True
except ImportError:
    # Qt not available - will use Pillow fallback
    QImage = None  # type: ignore[assignment, misc]
    QColor = None  # type: ignore[assignment, misc]
    QPainter = None  # type: ignore[assignment, misc]
    QPainterPath = None  # type: ignore[assignment, misc]

# Pillow fallback for minimap generation
PIL_AVAILABLE = False
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    Image = None  # type: ignore[assignment, misc]
    ImageDraw = None  # type: ignore[assignment, misc]


def _get_resource_priority(location: LocationResult, installation: Installation) -> int:
    """Get resource priority based on KOTOR resolution order.
    
    Resolution order (from highest to lowest priority):
    1. Override folder (priority 0 - highest)
    2. Modules (.mod files) (priority 1)
    3. Modules (.rim/_s.rim/_dlg.erf files) (priority 2)
    4. Chitin BIFs (priority 3 - lowest)
    
    Reference: Libraries/PyKotor/src/pykotor/tslpatcher/writer.py _get_resource_priority
    
    Args:
    ----
        location: LocationResult from installation.locations()
        installation: The installation instance
        
    Returns:
    -------
        Priority value (lower = higher priority)
    """
    filepath = location.filepath
    parent_names_lower = [parent.name.lower() for parent in filepath.parents]
    
    if "override" in parent_names_lower:
        return 0
    if "modules" in parent_names_lower:
        name_lower = filepath.name.lower()
        if name_lower.endswith(".mod"):
            return 1
        return 2  # .rim/_s.rim/_dlg.erf
    if "data" in parent_names_lower or filepath.suffix.lower() == ".bif":
        return 3
    # Files directly in installation root treated as Override priority
    if filepath.parent == installation.path():
        return 0
    # Default to lowest priority if unknown
    return 3


def _resolve_resource_with_priority(
    installation: Installation,
    resname: str,
    restype: ResourceType,
    logger: RobustLogger | None = None,
) -> bytes | None:
    """Resolve a resource using KOTOR resolution order priority and return its data.
    
    Follows KOTOR's resource resolution order:
    1. Override folder (highest priority)
    2. Modules (.mod files)
    3. Modules (.rim/_s.rim/_dlg.erf files)
    4. Chitin BIFs (lowest priority)
    
    Reference: Libraries/PyKotor/src/pykotor/tslpatcher/diff/resolution.py resolve_resource_in_installation
    Reference: Libraries/PyKotor/src/pykotor/tslpatcher/writer.py _get_resource_priority
    
    Args:
    ----
        installation: The game installation instance
        resname: Resource name (e.g., "m28ab_01a")
        restype: Resource type (e.g., ResourceType.MDL)
        logger: Optional logger for debugging
        
    Returns:
    -------
        Resource data bytes for the highest priority resource, or None if not found
    """
    if logger is None:
        logger = RobustLogger()
    
    # Find all locations for this resource
    identifier = ResourceIdentifier(resname=resname, restype=restype)
    locations_result = installation.locations(
        [identifier],
        [
            SearchLocation.OVERRIDE,
            SearchLocation.MODULES,
            SearchLocation.CHITIN,
        ],
    )
    
    location_list = locations_result.get(identifier, [])
    if not location_list:
        return None
    
    # Sort by priority (lower priority number = higher priority)
    # If multiple resources exist, use the one with highest priority (lowest number)
    location_list_sorted = sorted(
        location_list,
        key=lambda loc: _get_resource_priority(loc, installation),
    )
    
    # Get the highest priority location
    best_location = location_list_sorted[0]
    
    # Get priority for logging
    priority = _get_resource_priority(best_location, installation)
    priority_names = ["Override", "Modules (.mod)", "Modules (.rim)", "Chitin"]
    if logger and len(location_list) > 1:
        logger.debug(f"Found {len(location_list)} locations for {resname}.{restype.extension}, using {priority_names[priority]} (highest priority)")
    
    # Read the resource data
    try:
        with best_location.filepath.open("rb") as f:
            f.seek(best_location.offset)
            data = f.read(best_location.size)
        return data
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to read resource {resname}.{restype.extension} from {best_location.filepath}: {e}")
        return None


def find_module_file(installation: Installation, module_name: str) -> Path | None:
    """Find the path to a module's main RIM file.
    
    Searches in both the rims and modules directories of the installation.
    
    Args:
    ----
        installation: The game installation instance
        module_name: The module name (e.g., "danm13")
        
    Returns:
    -------
        Path to the module's main RIM file if found, None otherwise
    """
    rims_path = installation.rims_path()
    modules_path = installation.module_path()
    
    # Check rims_path first, then modules_path
    if rims_path and rims_path.exists():
        main_rim = rims_path / f"{module_name}.rim"
        if main_rim.exists():
            return main_rim
    if modules_path and modules_path.exists():
        main_rim = modules_path / f"{module_name}.rim"
        if main_rim.exists():
            return main_rim
    return None


def extract_kit(
    installation: Installation,
    module_name: str,
    output_path: Path,
    *,
    kit_id: str | None = None,
    logger: RobustLogger | None = None,
) -> None:
    """Extract kit resources from module RIM or ERF files.

    Supports both RIM files (module_name.rim, module_name_s.rim) and ERF files
    (module_name.mod, module_name.erf, module_name.hak, module_name.sav).

    Args:
    ----
        installation: The game installation instance
        module_name: The module name (e.g., "danm13" or "danm13.mod")
        output_path: Path where the kit should be generated
        kit_id: Optional kit identifier (defaults to module_name.lower())
        logger: Optional logger instance for progress reporting

    Processing Logic:
    -----------------
        1. Determine file type from module_name extension or search for RIM/ERF files
        2. Load archive files (RIM or ERF)
        3. Extract all relevant resources (MDL, MDX, WOK, PWK, DWK, TGA, TXI, UTD, UTP)
        4. Extract WOK files from LYT room models
        5. Extract PWK files from placeable models (UTP -> placeables.2da -> modelname.pwk)
        6. Extract DWK files from door models (UTD -> genericdoors.2da -> modelname0/1/2.dwk)
        7. Organize resources into kit structure
        8. Generate JSON file with component definitions
        
    References:
    ----------
        vendor/reone/src/libs/game/object/door.cpp:80-94 - DWK extraction (modelname0/1/2.dwk)
        vendor/reone/src/libs/game/object/placeable.cpp:73 - PWK extraction (modelname.pwk)
        vendor/KotOR.js/src/module/ModuleRoom.ts:331-342 - WOK loading for rooms
        vendor/KotOR.js/src/module/ModuleDoor.ts:992 - DWK loading
        vendor/KotOR.js/src/module/ModulePlaceable.ts:684 - PWK loading

    Raises:
    ------
        FileNotFoundError: If no valid RIM or ERF files are found for the module
        ValueError: If the module name format is invalid
    """
    if logger is None:
        logger = RobustLogger()
    
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Sanitize module name and extract clean name
    module_path = Path(module_name)
    module_name_clean = module_path.stem.lower()
    logger.info(f"Processing module: {module_name_clean}")

    if kit_id is None:
        kit_id = module_name_clean
    
    # Sanitize kit_id (remove invalid filename characters)
    kit_id = re.sub(r'[<>:"/\\|?*]', '_', str(kit_id))
    kit_id = kit_id.strip('. ')
    if not kit_id:
        kit_id = module_name_clean
    kit_id = kit_id.lower()

    # Determine file type from extension
    extension = module_path.suffix.lower() if module_path.suffix else None

    # ERF extensions: .erf, .mod, .hak, .sav
    # RIM extension: .rim
    is_erf = extension in {".erf", ".mod", ".hak", ".sav"}
    is_rim = extension == ".rim"

    rims_path = installation.rims_path()
    modules_path = installation.module_path()
    
    main_archive: RIM | ERF | None = None
    data_archive: RIM | ERF | None = None
    using_dot_mod: bool = False  # Track if we're using a .mod file (affects Module class initialization)

    if is_erf:
        # ERF file specified - try to load it directly or search for it
        logger.info(f"Detected ERF format from extension: {extension}")
        erf_path = None

        # If it's a full path, use it directly
        if module_path.is_absolute() or module_path.exists():
            erf_path = module_path
        else:
            # Search in modules directory - prioritize .mod files (they override .rim files)
            for ext in [".mod", ".erf", ".hak", ".sav"]:  # .mod first!
                candidate = modules_path / f"{module_name_clean}{ext}"
                if candidate.exists():
                    erf_path = candidate
                    if ext == ".mod":
                        using_dot_mod = True
                        logger.info(f"Found .mod file: {candidate} - will use .mod format")
                    break

        if erf_path and erf_path.exists():
            logger.info(f"Loading ERF file: {erf_path}")
            # Check if this is a .mod file
            if extension == ".mod" or (erf_path.suffix.lower() == ".mod"):
                using_dot_mod = True
                logger.info("Detected .mod file - will use .mod format for Module class")
            try:
                main_archive = read_erf(erf_path)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to read ERF file '{erf_path}': {e}")
                raise
        else:
            raise FileNotFoundError(f"ERF file not found: {module_name}")

    elif is_rim:
        # RIM file specified - try to load it directly or search for it
        logger.info("Detected RIM format from extension")
        rim_path = None

        # If it's a full path, use it directly
        if module_path.is_absolute() or module_path.exists():
            rim_path = module_path
        else:
            # Search in rims and modules directories
            for search_path in [rims_path, modules_path]:
                if search_path and search_path.exists():
                    candidate = search_path / f"{module_name_clean}.rim"
                    if candidate.exists():
                        rim_path = candidate
                        break

        if rim_path and rim_path.exists():
            logger.info(f"Loading RIM file: {rim_path}")
            try:
                main_archive = read_rim(rim_path)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to read RIM file '{rim_path}': {e}")
                raise
        else:
            raise FileNotFoundError(f"RIM file not found: {module_name}")

    else:
        # No extension - search for both RIM and ERF files
        # PRIORITY: .mod files take precedence over .rim files (as per KOTOR resolution order)
        logger.info("No extension detected, searching for RIM or ERF files...")

        # FIRST: Check for .mod file (highest priority - .mod files override .rim files)
        erf_path = None
        if modules_path and modules_path.exists():
            # Check for .mod first (highest priority)
            mod_candidate = modules_path / f"{module_name_clean}.mod"
            if mod_candidate.exists():
                erf_path = mod_candidate
                using_dot_mod = True
                logger.info(f"Found .mod file: {erf_path} (using .mod format, will ignore .rim files)")
            else:
                # Try other ERF files (but not .mod, already checked)
                for ext in [".erf", ".hak", ".sav"]:
                    candidate = modules_path / f"{module_name_clean}{ext}"
                    if candidate.exists():
                        erf_path = candidate
                        break

        # If .mod file found, use it (don't check for .rim files)
        if erf_path and erf_path.exists() and using_dot_mod:
            logger.info(f"Loading .mod file: {erf_path}")
            try:
                main_archive = read_erf(erf_path)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to read ERF file '{erf_path}': {e}")
                raise
        elif erf_path and erf_path.exists():
            # Other ERF file (not .mod)
            logger.info(f"Found ERF file: {erf_path}")
            try:
                main_archive = read_erf(erf_path)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to read ERF file '{erf_path}': {e}")
                raise
        else:
            # No ERF file found, try RIM files
            main_rim_path = None
            data_rim_path = None

            for search_path in [rims_path, modules_path]:
                if search_path and search_path.exists():
                    candidate_main = search_path / f"{module_name_clean}.rim"
                    candidate_data = search_path / f"{module_name_clean}_s.rim"
                    if candidate_main.exists():
                        main_rim_path = candidate_main
                    if candidate_data.exists():
                        data_rim_path = candidate_data

            if main_rim_path or data_rim_path:
                logger.info(f"Found RIM files: main={main_rim_path}, data={data_rim_path}")
                if main_rim_path and main_rim_path.exists():
                    try:
                        main_archive = read_rim(main_rim_path)
                    except Exception as e:  # noqa: BLE001
                        logger.error(f"Failed to read RIM file '{main_rim_path}': {e}")
                        raise
                if data_rim_path and data_rim_path.exists():
                    try:
                        data_archive = read_rim(data_rim_path)
                    except Exception as e:  # noqa: BLE001
                        logger.error(f"Failed to read RIM file '{data_rim_path}': {e}")
                        raise
            else:
                msg = f"Neither RIM nor ERF files found for module '{module_name_clean}'"
                raise FileNotFoundError(msg)

    if main_archive is None and data_archive is None:
        msg = f"No valid archive files found for module '{module_name_clean}'"
        raise FileNotFoundError(msg)

    # Collect all resources from archive files
    all_resources: dict[tuple[str, ResourceType], bytes] = {}
    logger.info("Collecting resources from archive files...")

    for archive in [main_archive, data_archive]:
        if archive is None:
            continue
        resource_count = 0
        for resource in archive:  # Both RIM and ERF are iterable and yield ArchiveResource objects
            key = (str(resource.resref).lower(), resource.restype)
            if key not in all_resources:
                all_resources[key] = resource.data
                resource_count += 1
        logger.info(f"  Extracted {resource_count} resources from archive")

    logger.info(f"Total unique resources collected: {len(all_resources)}")

    # Organize resources by type
    components: dict[str, dict[str, bytes]] = {}  # component_id -> {mdl, mdx, wok}
    textures: dict[str, bytes] = {}  # texture_name -> tga_data
    texture_txis: dict[str, bytes] = {}  # texture_name -> txi_data
    lightmaps: dict[str, bytes] = {}  # lightmap_name -> tga_data
    lightmap_txis: dict[str, bytes] = {}  # lightmap_name -> txi_data
    doors: dict[str, bytes] = {}  # door_name -> utd_data
    door_walkmeshes: dict[str, dict[str, bytes]] = {}  # door_name -> {dwk0, dwk1, dwk2}
    placeables: dict[str, bytes] = {}  # placeable_name -> utp_data
    placeable_walkmeshes: dict[str, bytes] = {}  # placeable_model_name -> pwk_data
    skyboxes: dict[str, dict[str, bytes]] = {}  # skybox_name -> {mdl, mdx}
    all_models: dict[str, dict[str, bytes]] = {}  # model_name -> {mdl, mdx} (all models, not just components)

    # Create a Module instance to access all module resources (including from chitin)
    # This is needed to get LYT room models and GIT placeables/doors
    # Use use_dot_mod=True if we detected a .mod file (it takes priority over .rim files)
    module = Module(module_name_clean, installation, use_dot_mod=using_dot_mod)
    if using_dot_mod:
        logger.info(f"Using .mod format for Module class (module_name: {module_name_clean})")
    else:
        logger.info(f"Using .rim format for Module class (module_name: {module_name_clean})")
    
    # Get LYT to find all room models (which have WOK files)
    # Reference: vendor/reone/src/libs/game/object/area.cpp (room loading)
    # Reference: vendor/KotOR.js/src/module/ModuleRoom.ts:331-342 (loadWalkmesh)
    lyt_resource = module.layout()
    lyt_room_models: set[str] = set()  # Store lowercase room model names
    lyt_room_model_names: list[str] = []  # Store original room model names (for resource lookup)
    lyt = None
    if lyt_resource:
        lyt = lyt_resource.resource()
        if lyt:
            # Store original room model names for resource lookup
            lyt_room_model_names = list(lyt.all_room_models())
            # Normalize all room model names to lowercase for consistent comparison
            lyt_room_models = {model.lower() for model in lyt_room_model_names}
            # Extract WOK files for all LYT room models (even if not in RIM)
            # Use installation-wide resolution to respect priority order
            # Reference: LYT.iter_resource_identifiers() yields WOK for each room
            for room_model in lyt_room_model_names:
                wok_data = _resolve_resource_with_priority(installation, room_model, ResourceType.WOK, logger)
                if wok_data:
                    # Add WOK to all_resources if not already present (use lowercase key)
                    wok_key = (room_model.lower(), ResourceType.WOK)
                    if wok_key not in all_resources:
                        all_resources[wok_key] = wok_data
    
    # Identify components (MDL files that have corresponding WOK files)
    # Components are room models from LYT that have WOK walkmeshes
    logger.info(f"Found {len(lyt_room_models)} room models in LYT: {sorted(list(lyt_room_models))[:10]}...")
    
    # First, identify components directly from LYT room models
    # Use installation-wide resolution to respect priority order: Override > Modules (.mod) > Modules (.rim) > Chitin
    for room_model in lyt_room_model_names:
        room_model_lower = room_model.lower()
        
        # Get MDL, MDX, and WOK using installation-wide resolution with proper priority
        # This ensures we get the highest priority version (e.g., from Override if it exists)
        mdl_data = _resolve_resource_with_priority(installation, room_model, ResourceType.MDL, logger)
        mdx_data_raw = _resolve_resource_with_priority(installation, room_model, ResourceType.MDX, logger)
        wok_data = _resolve_resource_with_priority(installation, room_model, ResourceType.WOK, logger)
        
        if mdl_data and wok_data:
            # Ensure mdx_data is bytes (not None)
            mdx_data: bytes = mdx_data_raw if mdx_data_raw else b""
            
            # Store in components
            components[room_model_lower] = {
                "mdl": mdl_data,
                "mdx": mdx_data,
                "wok": wok_data,
            }
            
            # Also store in all_models
            if room_model_lower not in all_models:
                all_models[room_model_lower] = {
                    "mdl": mdl_data,
                    "mdx": mdx_data,
                }
            
            # Ensure WOK is in all_resources for consistency
            wok_key = (room_model_lower, ResourceType.WOK)
            if wok_key not in all_resources:
                all_resources[wok_key] = wok_data
            
            logger.debug(f"Identified component: {room_model_lower} (room model with WOK, resolved with priority)")
        else:
            logger.debug(f"Skipping room model {room_model_lower}: MDL or WOK resource not found")
    
    # Also check resources from RIM/ERF archives for components (in case some are there)
    for (resname, restype), data in all_resources.items():
        if restype == ResourceType.MDL:
            # All keys in all_resources are lowercase, so use lowercase for lookups
            resname_lower = resname.lower()  # resname is already lowercase from all_resources keys
            wok_key = (resname_lower, ResourceType.WOK)
            mdx_key = (resname_lower, ResourceType.MDX)
            
            # Store all models (for comprehensive extraction)
            if resname_lower not in all_models:
                all_models[resname_lower] = {
                    "mdl": data,
                    "mdx": all_resources.get(mdx_key, b""),
                }
            
            # Components are room models (from LYT) with WOK files
            # Only add if not already added from LYT room models above
            is_room_model = resname_lower in lyt_room_models
            has_wok = wok_key in all_resources
            if is_room_model and has_wok and resname_lower not in components:
                components[resname_lower] = {
                    "mdl": data,
                    "mdx": all_resources.get(mdx_key, b""),
                    "wok": all_resources[wok_key],
                }
                logger.debug(f"Identified component: {resname_lower} (room model with WOK from RIM)")
        elif restype == ResourceType.UTD:
            doors[resname] = data
        elif restype == ResourceType.UTP:
            placeables[resname] = data
        elif restype == ResourceType.MDX:
            # All keys in all_resources are lowercase, so use lowercase for lookups
            resname_lower = resname.lower()  # resname is already lowercase from all_resources keys
            mdl_key = (resname_lower, ResourceType.MDL)
            wok_key = (resname_lower, ResourceType.WOK)
            if mdl_key in all_resources and wok_key not in all_resources:
                # Likely a skybox
                skyboxes[resname_lower] = {
                    "mdl": all_resources[mdl_key],
                    "mdx": data,
                }
            # Also store MDX in all_models if MDL exists
            if mdl_key in all_resources and resname_lower not in all_models:
                all_models[resname_lower] = {
                    "mdl": all_resources[mdl_key],
                    "mdx": data,
                }

    logger.info(f"Identified {len(components)} components: {sorted(list(components.keys()))[:10]}...")
    
    # Extract textures and lightmaps from MDL files using iterate_textures/iterate_lightmaps
    # This is the same approach used in main.py _extract_mdl_textures
    # Use Module class to get all models (including from chitin) that reference textures/lightmaps
    all_texture_names: set[str] = set()
    all_lightmap_names: set[str] = set()

    # Get all models from the module (including those loaded from chitin)
    for model_resource in module.models():
        try:
            model_data = model_resource.data()
            if model_data:
                all_texture_names.update(iterate_textures(model_data))
                all_lightmap_names.update(iterate_lightmaps(model_data))
        except Exception:  # noqa: BLE001
            # Skip models that can't be loaded
            pass

    # Also extract all TPC/TGA files from RIM that might be textures/lightmaps
    # Some kits (like jedienclave) only have textures/lightmaps without components
    for (resname, restype), data in all_resources.items():
        if restype == ResourceType.TPC:
            # Determine if it's a texture or lightmap based on naming
            resname_lower = resname.lower()
            if "_lm" in resname_lower or resname_lower.endswith("_lm"):
                all_lightmap_names.add(resname)
            else:
                all_texture_names.add(resname)
        elif restype == ResourceType.TGA:
            # Determine if it's a texture or lightmap based on naming
            resname_lower = resname.lower()
            if "_lm" in resname_lower or resname_lower.endswith("_lm"):
                all_lightmap_names.add(resname)
            else:
                all_texture_names.add(resname)
    
    # Also check module resources for textures that might not be in RIM files
    # This catches textures that are in the module but not directly in the RIM
    for res_ident, loc_list in module.resources.items():
        if res_ident.restype in (ResourceType.TPC, ResourceType.TGA):
            resname_lower = res_ident.resname.lower()
            if "_lm" in resname_lower or resname_lower.endswith("_lm") or resname_lower.startswith("l_"):
                all_lightmap_names.add(res_ident.resname)
            else:
                all_texture_names.add(res_ident.resname)

    # Batch all texture/lightmap lookups to avoid checking all files multiple times
    # This is a major performance optimization - instead of calling installation.locations()
    # 136+ times (once per texture), we call it once with all textures
    all_texture_identifiers: list[ResourceIdentifier] = []
    for name in all_texture_names:
        all_texture_identifiers.append(ResourceIdentifier(resname=name, restype=ResourceType.TPC))
        all_texture_identifiers.append(ResourceIdentifier(resname=name, restype=ResourceType.TGA))
    for name in all_lightmap_names:
        all_texture_identifiers.append(ResourceIdentifier(resname=name, restype=ResourceType.TPC))
        all_texture_identifiers.append(ResourceIdentifier(resname=name, restype=ResourceType.TGA))
    
    # Single batch lookup for all textures/lightmaps
    # Include MODULES in search order to respect resolution priority: Override > Modules > Textures > Chitin
    logger.info(f"Batch looking up {len(all_texture_identifiers)} texture/lightmap resources...")
    batch_location_results: dict[ResourceIdentifier, list[LocationResult]] = installation.locations(
        all_texture_identifiers,
        [
            SearchLocation.OVERRIDE,
            SearchLocation.MODULES,  # Check modules (.mod/.rim) before texture packs
            SearchLocation.TEXTURES_GUI,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.CHITIN,
        ],
    )
    logger.info(f"Found locations for {len([r for r in batch_location_results.values() if r])} resources")
    
    # Batch all TXI lookups upfront to avoid expensive individual calls
    # This is a major performance optimization - instead of calling installation.locations()
    # individually for each texture/lightmap (potentially 100+ times), we call it once
    all_txi_identifiers: list[ResourceIdentifier] = []
    for name in all_texture_names:
        all_txi_identifiers.append(ResourceIdentifier(resname=name, restype=ResourceType.TXI))
    for name in all_lightmap_names:
        all_txi_identifiers.append(ResourceIdentifier(resname=name, restype=ResourceType.TXI))
    
    logger.info(f"Batch looking up {len(all_txi_identifiers)} TXI resources...")
    batch_txi_location_results: dict[ResourceIdentifier, list[LocationResult]] = installation.locations(
        all_txi_identifiers,
        [
            SearchLocation.OVERRIDE,
            SearchLocation.MODULES,  # Check modules (.mod/.rim) before texture packs
            SearchLocation.TEXTURES_GUI,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.CHITIN,
        ],
    )
    logger.info(f"Found locations for {len([r for r in batch_txi_location_results.values() if r])} TXI resources")

    def extract_texture_or_lightmap(name: str, is_lightmap: bool) -> None:
        """Extract a texture or lightmap from RIM files or installation.
        
        This matches the implementation in Tools/HolocronToolset/src/toolset/gui/windows/main.py
        _locate_texture, _process_texture, and _save_texture methods.
        """
        name_lower: str = name.lower()
        target_dict: dict[str, bytes] = lightmaps if is_lightmap else textures
        target_txis: dict[str, bytes] = lightmap_txis if is_lightmap else texture_txis
        
        if name_lower in target_dict:
            return  # Already extracted
        
        # Use pre-fetched batch location results instead of calling installation.locations() again
        # This avoids checking all files multiple times (major performance improvement)
        try:
            # Look up in batch results
            location_results: dict[ResourceIdentifier, list[LocationResult]] = {}
            for rt in (ResourceType.TPC, ResourceType.TGA):
                res_ident = ResourceIdentifier(resname=name, restype=rt)
                if res_ident in batch_location_results:
                    location_results[res_ident] = batch_location_results[res_ident]
            
            # Process like main.py _process_texture and _save_texture
            # Prioritize locations: select highest priority location (Override > Modules > Textures > Chitin)
            for res_ident, loc_list in location_results.items():
                if not loc_list:
                    continue
                
                # Sort by priority and select highest priority location
                loc_list_sorted = sorted(
                    loc_list,
                    key=lambda loc: _get_resource_priority(loc, installation),
                )
                location: LocationResult = loc_list_sorted[0]
                
                # Always convert to TGA format (like main.py with tpcDecompileCheckbox)
                if res_ident.restype == ResourceType.TPC:
                    # Read TPC from location
                    with location.filepath.open("rb") as f:
                        f.seek(location.offset)
                        tpc_data = f.read(location.size)
                    try:
                        tpc = read_tpc(tpc_data)
                        tga_data = bytearray()
                        write_tpc(tpc, tga_data, ResourceType.TGA)
                        target_dict[name_lower] = bytes(tga_data)
                        # Extract TXI if present (like main.py _extract_txi)
                        if tpc.txi and tpc.txi.strip():
                            target_txis[name_lower] = tpc.txi.encode("ascii", errors="ignore")
                    except Exception:  # noqa: BLE001
                        # If TPC can't be read, skip it
                        continue
                else:
                    # TGA file - read directly
                    with location.filepath.open("rb") as f:
                        f.seek(location.offset)
                        target_dict[name_lower] = f.read(location.size)
                # Try to find corresponding TXI file from pre-batched results
                # Only if we haven't already extracted TXI from TPC
                if name_lower not in target_txis:
                    # Look up in pre-batched TXI results
                    txi_res_ident = ResourceIdentifier(resname=name, restype=ResourceType.TXI)
                    if txi_res_ident in batch_txi_location_results:
                        txi_loc_list = batch_txi_location_results[txi_res_ident]
                        if txi_loc_list:
                            try:
                                # Prioritize locations and select highest priority
                                txi_loc_list_sorted = sorted(
                                    txi_loc_list,
                                    key=lambda loc: _get_resource_priority(loc, installation),
                                )
                                txi_location = txi_loc_list_sorted[0]
                                with txi_location.filepath.open("rb") as f:
                                    f.seek(txi_location.offset)
                                    target_txis[name_lower] = f.read(txi_location.size)
                            except Exception:  # noqa: BLE001
                                pass
                break  # Use first available location
        except Exception:  # noqa: BLE001
            pass  # Texture/lightmap not found, skip it

    # Extract all textures
    for texture_name in all_texture_names:
        extract_texture_or_lightmap(texture_name, is_lightmap=False)

    # Extract all lightmaps
    for lightmap_name in all_lightmap_names:
        extract_texture_or_lightmap(lightmap_name, is_lightmap=True)
    
    # After extracting all textures/lightmaps, try to find TXI files for any that don't have them yet
    # Use pre-batched TXI results instead of individual installation.locations() calls
    # This is a major performance optimization
    texture_name_map: dict[str, str] = {}  # Map lowercase -> original case
    for orig_name in all_texture_names:
        texture_name_map[orig_name.lower()] = orig_name
    
    missing_txi_count: int = 0
    found_txi_count: int = 0
    
    for texture_name_lower in textures.keys():
        if texture_name_lower not in texture_txis:
            missing_txi_count += 1
            # Try to find TXI file from pre-batched results
            # Try both lowercase and original case
            names_to_try_tx = [texture_name_lower]
            if texture_name_lower in texture_name_map:
                orig_name = texture_name_map[texture_name_lower]
                if orig_name != texture_name_lower:
                    names_to_try_tx.append(orig_name)
            
            found: bool = False
            for name_to_try_tx in names_to_try_tx:
                txi_res_ident = ResourceIdentifier(resname=name_to_try_tx, restype=ResourceType.TXI)
                if txi_res_ident in batch_txi_location_results:
                    txi_loc_list = batch_txi_location_results[txi_res_ident]
                    if txi_loc_list:
                        try:
                            # Prioritize locations and select highest priority
                            txi_loc_list_sorted = sorted(
                                txi_loc_list,
                                key=lambda loc: _get_resource_priority(loc, installation),
                            )
                            txi_location = txi_loc_list_sorted[0]
                            with txi_location.filepath.open("rb") as f:
                                f.seek(txi_location.offset)
                                texture_txis[texture_name_lower] = f.read(txi_location.size)
                            found = True
                            found_txi_count += 1
                            break
                        except Exception:  # noqa: BLE001
                            pass
            
            if not found:
                # Create empty TXI file as placeholder (many TXI files in the game are empty)
                # This matches the expected kit structure where textures have corresponding TXI files
                texture_txis[texture_name_lower] = b""
    
    # Same for lightmaps - use pre-batched TXI results
    lightmap_name_map: dict[str, str] = {}  # Map lowercase -> original case
    for orig_name in all_lightmap_names:
        lightmap_name_map[orig_name.lower()] = orig_name
    
    missing_lm_txi_count = 0
    found_lm_txi_count = 0
    
    for lightmap_name_lower in lightmaps.keys():
        if lightmap_name_lower not in lightmap_txis:
            missing_lm_txi_count += 1
            # Try to find TXI file from pre-batched results
            # Try both lowercase and original case
            names_to_try_lm: list[str] = [lightmap_name_lower]
            if lightmap_name_lower in lightmap_name_map:
                orig_name = lightmap_name_map[lightmap_name_lower]
                if orig_name != lightmap_name_lower:
                    names_to_try_lm.append(orig_name)
            
            found_lm = False
            for name_to_try_lm in names_to_try_lm:
                txi_res_ident = ResourceIdentifier(resname=name_to_try_lm, restype=ResourceType.TXI)
                if txi_res_ident in batch_txi_location_results:
                    txi_loc_list = batch_txi_location_results[txi_res_ident]
                    if txi_loc_list:
                        try:
                            # Prioritize locations and select highest priority
                            txi_loc_list_sorted = sorted(
                                txi_loc_list,
                                key=lambda loc: _get_resource_priority(loc, installation),
                            )
                            txi_location = txi_loc_list_sorted[0]
                            with txi_location.filepath.open("rb") as f:
                                f.seek(txi_location.offset)
                                lightmap_txis[lightmap_name_lower] = f.read(txi_location.size)
                            found_lm = True
                            found_lm_txi_count += 1
                            break
                        except Exception:  # noqa: BLE001
                            pass
                if found_lm:
                    break  # Found it, no need to try other names
            
            if not found_lm:
                # Create empty TXI file as placeholder (many TXI files in the game are empty)
                lightmap_txis[lightmap_name_lower] = b""

    # Create kit directory structure
    kit_dir: Path = output_path / kit_id
    kit_dir.mkdir(parents=True, exist_ok=True)

    textures_dir: Path = kit_dir / "textures"
    textures_dir.mkdir(exist_ok=True)
    lightmaps_dir: Path = kit_dir / "lightmaps"
    lightmaps_dir.mkdir(exist_ok=True)
    skyboxes_dir: Path = kit_dir / "skyboxes"
    skyboxes_dir.mkdir(exist_ok=True)

    # Write component files
    component_list: list[dict[str, str | int | list[dict]]] = []
    for component_id, component_data in components.items():
        # Write component files directly in kit_dir (not in subdirectory)
        (kit_dir / f"{component_id}.mdl").write_bytes(component_data["mdl"])
        if component_data["mdx"]:
            (kit_dir / f"{component_id}.mdx").write_bytes(component_data["mdx"])

        # CRITICAL: Re-center BWM around (0, 0) before saving!
        # Game WOKs are in world coordinates, but Indoor Map Builder expects
        # centered BWMs so that the preview image aligns with the walkmesh hitbox.
        # Without this, images render in one place but hitboxes are elsewhere.
        bwm: BWM = read_bwm(component_data["wok"])
        bwm = _recenter_bwm(bwm)
        
        # Write the re-centered WOK file
        (kit_dir / f"{component_id}.wok").write_bytes(bytes_bwm(bwm))

        # Generate minimap PNG from re-centered BWM
        minimap_image = _generate_component_minimap(bwm)
        minimap_path: Path = kit_dir / f"{component_id}.png"
        # Save image - both QImage and PIL Image support save() with same signature
        minimap_image.save(str(minimap_path), "PNG")

        # Extract doorhooks from re-centered BWM edges with transitions
        doorhooks: list[dict] = _extract_doorhooks_from_bwm(bwm, len(doors))

        # Create component entry with extracted doorhooks
        component_list.append({
            "name": component_id.replace("_", " ").title(),
            "id": component_id,
            "native": 1,
            "doorhooks": doorhooks,
        })

    # Write texture files
    for texture_name, texture_data in textures.items():
        (textures_dir / f"{texture_name}.tga").write_bytes(texture_data)
        # Always write TXI file (even if empty) to match expected kit structure
        if texture_name in texture_txis:
            (textures_dir / f"{texture_name}.txi").write_bytes(texture_txis[texture_name])
        else:
            # Create empty TXI placeholder if not found
            (textures_dir / f"{texture_name}.txi").write_bytes(b"")

    # Write lightmap files
    for lightmap_name, lightmap_data in lightmaps.items():
        (lightmaps_dir / f"{lightmap_name}.tga").write_bytes(lightmap_data)
        # Always write TXI file (even if empty) to match expected kit structure
        if lightmap_name in lightmap_txis:
            (lightmaps_dir / f"{lightmap_name}.txi").write_bytes(lightmap_txis[lightmap_name])
        else:
            # Create empty TXI placeholder if not found
            (lightmaps_dir / f"{lightmap_name}.txi").write_bytes(b"")

    # Extract door walkmeshes (DWK files)
    # Reference: vendor/reone/src/libs/game/object/door.cpp:80-94
    # Doors have 3 walkmesh states: closed (0), open1 (1), open2 (2)
    # Format: <modelname>0.dwk, <modelname>1.dwk, <modelname>2.dwk
    for door_name, door_data in doors.items():
        door_walkmeshes[door_name] = door_tools.extract_door_walkmeshes(
            door_data,
            installation,
            module=module,
            logger=logger,
        )
    
    # Extract placeable walkmeshes (PWK files)
    # Reference: vendor/reone/src/libs/game/object/placeable.cpp:73
    # Format: <modelname>.pwk
    from pykotor.tools import placeable as placeable_tools
    
    for placeable_name, placeable_data in placeables.items():
        result = placeable_tools.extract_placeable_walkmesh(
            placeable_data,
            installation,
            module=module,
            logger=logger,
        )
        if result:
            placeable_model_name, pwk_data = result
            placeable_walkmeshes[placeable_model_name] = pwk_data
            logger.debug(f"Found PWK '{placeable_model_name}' for placeable '{placeable_name}'")

    # Write door files
    # Use simple door identifiers (door0, door1, etc.) for file names and JSON
    # This matches the expected kit format from the examples
    door_list: list[dict] = []
    for door_idx, (door_name, door_data) in enumerate(doors.items()):
        # Use simple identifier: door0, door1, door2, etc.
        door_id = f"door{door_idx}"
        
        # Write UTD files using the simple identifier
        (kit_dir / f"{door_id}_k1.utd").write_bytes(door_data)
        # For K1, we use the same UTD for K2 (in real kits, these might differ)
        (kit_dir / f"{door_id}_k2.utd").write_bytes(door_data)
        
        # Write door walkmeshes (DWK files) if found
        if door_name in door_walkmeshes:
            for dwk_key, dwk_data in door_walkmeshes[door_name].items():
                # Extract door model name to determine DWK filename
                try:
                    utd = read_utd(door_data)
                    genericdoors_2da = door_tools.load_genericdoors_2da(installation, logger)
                    if genericdoors_2da:
                        door_model_name = door_tools.get_model(utd, installation, genericdoors=genericdoors_2da)
                        if door_model_name:
                            # Map dwk_key (dwk0, dwk1, dwk2) to filename suffix (0, 1, 2)
                            dwk_suffix = dwk_key.replace("dwk", "")
                            dwk_filename = f"{door_model_name}{dwk_suffix}.dwk"
                            (kit_dir / dwk_filename).write_bytes(dwk_data)
                            logger.debug(f"Wrote door walkmesh '{dwk_filename}' for door '{door_id}' (resname: '{door_name}')")
                except Exception:  # noqa: BLE001
                    # Skip if we can't determine model name
                    pass
        
        # Extract width and height from door model or texture
        door_width, door_height = door_tools.get_door_dimensions(
            door_data,
            installation,
            door_name=door_name,
            logger=logger,
        )
        door_list.append({
            "utd_k1": f"{door_id}_k1",
            "utd_k2": f"{door_id}_k2",
            "width": door_width,
            "height": door_height,
        })

    # Write placeable walkmeshes (PWK files)
    for placeable_model_name, pwk_data in placeable_walkmeshes.items():
        (kit_dir / f"{placeable_model_name}.pwk").write_bytes(pwk_data)
        logger.debug(f"Wrote placeable walkmesh '{placeable_model_name}.pwk'")
    
    # Write all models (MDL/MDX) that aren't components or skyboxes
    # This ensures we extract all models referenced by the module, not just room components
    # Reference: Tools/HolocronToolset/src/toolset/gui/windows/main.py extractAllModuleModels
    models_dir: Path = kit_dir / "models"
    models_dir.mkdir(exist_ok=True)
    for model_name, model_data in all_models.items():
        # Skip if already written as component or skybox
        if model_name in components or model_name in skyboxes:
            continue
        # Write MDL and MDX files
        (models_dir / f"{model_name}.mdl").write_bytes(model_data["mdl"])
        if model_data.get("mdx"):
            (models_dir / f"{model_name}.mdx").write_bytes(model_data["mdx"])
        logger.debug(f"Wrote model '{model_name}' (MDL/MDX)")

    # Write skybox files
    for skybox_name, skybox_data in skyboxes.items():
        (skyboxes_dir / f"{skybox_name}.mdl").write_bytes(skybox_data["mdl"])
        (skyboxes_dir / f"{skybox_name}.mdx").write_bytes(skybox_data["mdx"])

    # Generate JSON file
    # Format kit name from kit_id (e.g., "enclavesurface" -> "Enclave Surface")
    kit_name = kit_id.replace("_", " ").title()
    kit_json = {
        "name": kit_name,
        "id": kit_id,
        "ht": "2.0.2",
        "version": 1,
        "components": component_list,
        "doors": door_list,
    }

    json_path: Path = output_path / f"{kit_id}.json"
    with json_path.open("w", encoding="utf-8") as f:  # type: ignore[assignment]
        json.dump(kit_json, f, indent=4, ensure_ascii=False)  # type: ignore[arg-type]


def _generate_component_minimap(bwm: BWM):  # type: ignore[return-value]
    """Generate a minimap PNG image from a BWM walkmesh.
    
    Uses Qt (QImage) if available, otherwise falls back to Pillow (PIL Image).
    
    Args:
    ----
        bwm: BWM walkmesh object
        
    Returns:
    -------
        QImage or PIL.Image: Minimap image (top-down view of walkmesh)
    """
    if not QT_AVAILABLE and not PIL_AVAILABLE:
        raise ImportError("Neither Qt bindings nor Pillow available - cannot generate minimap")
    
    # Calculate bounding box
    vertices: list[Vector3] = list(bwm.vertices())
    if not vertices:
        # Empty walkmesh - return small blank image
        if QT_AVAILABLE:
            image = QImage(256, 256, QImage.Format.Format_RGB888)  # type: ignore[misc, call-overload]
            image.fill(QColor(0, 0, 0))  # type: ignore[misc, call-overload]
            return image
        else:
            return Image.new("RGB", (256, 256), (0, 0, 0))  # type: ignore[misc, call-overload]
    
    bbmin: Vector3 = Vector3(min(v.x for v in vertices), min(v.y for v in vertices), min(v.z for v in vertices))
    bbmax: Vector3 = Vector3(max(v.x for v in vertices), max(v.y for v in vertices), max(v.z for v in vertices))
    
    # Add padding
    padding: float = 5.0
    bbmin.x -= padding
    bbmin.y -= padding
    bbmax.x += padding
    bbmax.y += padding
    
    # Calculate image dimensions (scale: 10 pixels per unit)
    width: int = int((bbmax.x - bbmin.x) * 10)
    height: int = int((bbmax.y - bbmin.y) * 10)
    
    # Ensure minimum size
    width = max(width, 256)
    height = max(height, 256)
    
    # Transform to image coordinates (flip Y, scale, translate)
    def to_image_coords(v: Vector2) -> tuple[float, float]:
        x = (v.x - bbmin.x) * 10
        y = height - (v.y - bbmin.y) * 10  # Flip Y
        return x, y
    
    # Use Qt if available
    if importlib.util.find_spec("qtpy") is not None:
        # Create image
        q_image: QImage | Image = QImage(width, height, QImage.Format.Format_RGB888)  # type: ignore[misc, call-overload]
        q_image.fill(QColor(0, 0, 0))  # type: ignore[misc, call-overload]
        
        # Draw walkmesh faces
        painter = QPainter(q_image)  # type: ignore[misc, call-overload]
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # type: ignore[misc, attr-defined]
        
        # Draw walkable faces in white, non-walkable in gray
        for face in bwm.faces:
            # Determine if face is walkable based on material
            is_walkable = face.material.value in (1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 22)
            color = QColor(255, 255, 255) if is_walkable else QColor(128, 128, 128)  # type: ignore[misc, call-overload]
            
            painter.setBrush(QColor(color))  # type: ignore[misc, call-overload]
            painter.setPen(QColor(color))  # type: ignore[misc, call-overload]
            
            # Build path from face vertices
            path = QPainterPath()  # type: ignore[misc, call-overload]
            v1 = Vector2(face.v1.x, face.v1.y)
            v2 = Vector2(face.v2.x, face.v2.y)
            v3 = Vector2(face.v3.x, face.v3.y)
            
            x1, y1 = to_image_coords(v1)
            x2, y2 = to_image_coords(v2)
            x3, y3 = to_image_coords(v3)
            
            path.moveTo(x1, y1)
            path.lineTo(x2, y2)
            path.lineTo(x3, y3)
            path.closeSubpath()
            
            painter.drawPath(path)
        
        painter.end()
        return q_image
    
    # Fallback to Pillow
    if importlib.util.find_spec("PIL") is not None:
        # Create image
        pil_image: Image = Image.new("RGB", (width, height), (0, 0, 0))  # type: ignore[misc, call-overload]
        draw: ImageDraw.Draw = ImageDraw.Draw(pil_image)  # type: ignore[misc, call-overload]
        
        # Draw walkable faces in white, non-walkable in gray
        for face in bwm.faces:
            # Determine if face is walkable based on material
            is_walkable = face.material.value in (1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 22)
            color = (255, 255, 255) if is_walkable else (128, 128, 128)
            
            # Get face vertices
            v1 = Vector2(face.v1.x, face.v1.y)
            v2 = Vector2(face.v2.x, face.v2.y)
            v3 = Vector2(face.v3.x, face.v3.y)
            
            x1, y1 = to_image_coords(v1)
            x2, y2 = to_image_coords(v2)
            x3, y3 = to_image_coords(v3)
            
            # Draw polygon (triangle)
            draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill=color, outline=color)
        
        return pil_image

    raise ImportError("Neither Qt bindings nor Pillow available - cannot generate minimap")


def _extract_doorhooks_from_bwm(bwm: BWM, num_doors: int) -> list[dict[str, float | int]]:
    """Extract doorhook positions from BWM edges with transitions.
    
    Args:
    ----
        bwm: BWM walkmesh object
        num_doors: Number of doors in the kit (for door index)
        
    Returns:
    -------
        list[dict[str, float | int]]: List of doorhook dictionaries with x, y, z, rotation, door, edge
    """
    doorhooks: list[dict[str, float | int]] = []
    
    # Get all perimeter edges (these are the edges with transitions)
    edges: list[BWMEdge] = bwm.edges()
    
    # Process edges with valid transitions
    for edge in edges:
        if edge.transition < 0:  # Skip edges without transitions
            continue
        
        face: BWMFace = edge.face
        # Get edge vertices based on local edge index (0, 1, or 2)
        # edge.index is the global edge index (face_index * 3 + local_edge_index)
        _face_index: int = edge.index // 3
        local_edge_index: int = edge.index % 3
        
        # Get vertices for this edge
        if local_edge_index == 0:
            v1 = face.v1
            v2 = face.v2
        elif local_edge_index == 1:
            v1 = face.v2
            v2 = face.v3
        else:  # local_edge_index == 2
            v1 = face.v3
            v2 = face.v1
        
        # Calculate midpoint of edge
        mid_x: float = (v1.x + v2.x) / 2.0
        mid_y: float = (v1.y + v2.y) / 2.0
        mid_z: float = (v1.z + v2.z) / 2.0
        
        # Calculate rotation (angle of edge in XY plane, in degrees)
        dx: float = v2.x - v1.x
        dy: float = v2.y - v1.y
        rotation = math.degrees(math.atan2(dy, dx))
        # Normalize to 0-360
        rotation = rotation % 360
        if rotation < 0:
            rotation += 360
        
        # Map transition index to door index
        # Transition indices typically map directly to door indices, but clamp to valid range
        door_index: int = min(edge.transition, num_doors - 1) if num_doors > 0 else 0
        
        doorhooks.append({
            "x": mid_x,
            "y": mid_y,
            "z": mid_z,
            "rotation": rotation,
            "door": door_index,
            "edge": edge.index,  # Global edge index
        })
    
    return doorhooks


def _recenter_bwm(bwm: BWM) -> BWM:
    """Re-center a BWM around (0, 0) so image and hitbox align in Indoor Map Builder.
    
    The Indoor Map Builder draws the preview image CENTERED at room.position,
    but translates the walkmesh BY room.position from its original coordinates.
    
    For these to align, the BWM must be centered around (0, 0):
    - If BWM center is at (100, 200) and room.position = (0, 0):
      - Image would be centered at (0, 0)
      - Walkmesh would be centered at (100, 200) after translate
      - MISMATCH! Image and hitbox are in different places.
    
    - After re-centering BWM to (0, 0):
      - Image is centered at room.position
      - Walkmesh is centered at room.position after translate
      - MATCH! Image and hitbox overlap perfectly.
    
    Args:
    ----
        bwm: BWM walkmesh object
        
    Returns:
    -------
        BWM: The same BWM object, modified in place and returned
    
    Reference:
    ---------
        Tools/HolocronToolset/src/toolset/gui/windows/indoor_builder.py - _draw_image()
        Tools/HolocronToolset/src/toolset/data/indoormap.py - IndoorMapRoom.walkmesh()
    """
    vertices: list[Vector3] = list(bwm.vertices())
    if not vertices:
        return bwm
    
    # Calculate current center
    min_x = min(v.x for v in vertices)
    max_x = max(v.x for v in vertices)
    min_y = min(v.y for v in vertices)
    max_y = max(v.y for v in vertices)
    min_z = min(v.z for v in vertices)
    max_z = max(v.z for v in vertices)
    
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    center_z = (min_z + max_z) / 2.0
    
    # Translate all vertices to center around origin
    # Use BWM.translate() which handles all vertices in faces
    bwm.translate(-center_x, -center_y, -center_z)
    
    return bwm

