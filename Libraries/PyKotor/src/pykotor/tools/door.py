from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.mdl import MDL, MDLNode, read_mdl
from pykotor.resource.formats.tpc import read_tpc
from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.generics.utd import UTD, read_utd
from pykotor.resource.type import ResourceType
from pykotor.tools.model import iterate_textures
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.common.module import Module
    from pykotor.extract.file import ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.resource.type import SOURCE_TYPES


def get_model(
    utd: UTD,
    installation: Installation,
    *,
    genericdoors: TwoDA | SOURCE_TYPES | None = None,
) -> str:
    """Returns the model name for the given door.
    
    References:
    ----------
        vendor/reone/src/libs/game/object/door.cpp (Door model lookup)
        vendor/KotOR.js/src/module/ModuleDoor.ts (Door appearance handling)
        Note: Door model lookup uses genericdoors.2da
    

    If no value is specified for the genericdoor parameters then it will be loaded from the given installation.

    Args:
    ----
        utd: UTD object of the door to lookup the model for.
        installation: The relevant installation.
        genericdoors: The genericdoors.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns the model name for the door.

    Raises:
    ------
        ValueError: genericdoors.2da not found in passed arguments OR the installation.
    """
    if genericdoors is None:
        result: ResourceResult | None = installation.resource("genericdoors", ResourceType.TwoDA)
        if not result:
            raise ValueError("Resource 'genericdoors.2da' not found in the installation, cannot get UTD model.")
        genericdoors = read_2da(result.data)
    if not isinstance(genericdoors, TwoDA):
        genericdoors = read_2da(genericdoors)

    return genericdoors.get_row(utd.appearance_id).get_string("modelname")


def load_genericdoors_2da(
    installation: Installation,
    logger: RobustLogger | None = None,
) -> TwoDA | None:
    """Load genericdoors.2da from installation using priority order.
    
    Tries locations() first (more reliable), then falls back to resource().
    Searches in Override first, then Chitin.
    
    Args:
    ----
        installation: The game installation instance
        logger: Optional logger for debugging
        
    Returns:
    -------
        TwoDA object if found, None otherwise
    """
    if logger is None:
        logger = RobustLogger()
    
    genericdoors_2da: TwoDA | None = None
    
    # Try locations() first (more reliable, handles BIF files)
    try:
        location_results = installation.locations(
            [ResourceIdentifier(resname="genericdoors", restype=ResourceType.TwoDA)],
            order=[SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        for res_ident, loc_list in location_results.items():
            if loc_list:
                loc = loc_list[0]  # Use first location (Override takes precedence)
                if loc.filepath and Path(loc.filepath).exists():
                    # Read from file (handles both direct files and BIF files)
                    with loc.filepath.open("rb") as f:
                        f.seek(loc.offset)
                        data = f.read(loc.size)
                    genericdoors_2da = read_2da(data)
                    break
    except Exception as e:  # noqa: BLE001
        logger.debug(f"locations() failed for genericdoors.2da: {e}")
    
    # Fallback: try resource() if locations() didn't work
    if genericdoors_2da is None:
        try:
            genericdoors_result = installation.resource("genericdoors", ResourceType.TwoDA)
            if genericdoors_result and genericdoors_result.data:
                genericdoors_2da = read_2da(genericdoors_result.data)
        except Exception as e:  # noqa: BLE001
            logger.debug(f"resource() also failed for genericdoors.2da: {e}")
    
    return genericdoors_2da


def extract_door_walkmeshes(
    utd_data: bytes,
    installation: Installation,
    *,
    module: Module | None = None,
    logger: RobustLogger | None = None,
) -> dict[str, bytes]:
    """Extract door walkmeshes (DWK files) for a door.
    
    Doors have 3 walkmesh states: closed (0), open1 (1), open2 (2)
    Format: <modelname>0.dwk, <modelname>1.dwk, <modelname>2.dwk
    
    References:
    ----------
        vendor/reone/src/libs/game/object/door.cpp:80-94 - DWK extraction (modelname0/1/2.dwk)
        vendor/reone/src/libs/game/object/door.cpp:66-67 - Door model lookup
        vendor/KotOR.js/src/module/ModuleDoor.ts:992 - DWK loading
    
    Args:
    ----
        utd_data: UTD door data bytes
        installation: The game installation instance
        module: Optional Module instance to search for DWK files in module resources first
        logger: Optional logger for debugging
        
    Returns:
    -------
        Dictionary mapping dwk_key ("dwk0", "dwk1", "dwk2") to DWK file data bytes
    """
    if logger is None:
        logger = RobustLogger()
    
    door_walkmeshes: dict[str, bytes] = {}
    
    try:
        utd = read_utd(utd_data)
        
        # Get door model name from UTD using genericdoors.2da
        genericdoors_2da = load_genericdoors_2da(installation, logger)
        if not genericdoors_2da:
            logger.debug("Could not load genericdoors.2da, cannot extract door walkmeshes")
            return door_walkmeshes
        
        door_model_name = get_model(utd, installation, genericdoors=genericdoors_2da)
        if not door_model_name:
            logger.debug(f"Could not get model name for door (appearance_id={utd.appearance_id})")
            return door_walkmeshes
        
        # Try to extract DWK files: modelname0.dwk, modelname1.dwk, modelname2.dwk
        dwk_variants = [
            (f"{door_model_name}0", "dwk0"),
            (f"{door_model_name}1", "dwk1"),
            (f"{door_model_name}2", "dwk2"),
        ]
        
        for dwk_resname, dwk_key in dwk_variants:
            try:
                # Try to find DWK in module resources first (if module provided)
                if module is not None:
                    dwk_resource = module.resource(dwk_resname, ResourceType.DWK)
                    if dwk_resource is not None:
                        dwk_data = dwk_resource.data()
                        if dwk_data:
                            door_walkmeshes[dwk_key] = dwk_data
                            logger.debug(f"Found DWK '{dwk_resname}' (state: {dwk_key}) from module")
                            continue
                
                # Try installation locations
                dwk_locations = installation.locations(
                    [ResourceIdentifier(resname=dwk_resname, restype=ResourceType.DWK)],
                    [
                        SearchLocation.OVERRIDE,
                        SearchLocation.MODULES,
                        SearchLocation.CHITIN,
                    ],
                )
                for dwk_ident, dwk_loc_list in dwk_locations.items():
                    if dwk_loc_list:
                        dwk_loc = dwk_loc_list[0]
                        with dwk_loc.filepath.open("rb") as f:
                            f.seek(dwk_loc.offset)
                            door_walkmeshes[dwk_key] = f.read(dwk_loc.size)
                        logger.debug(f"Found DWK '{dwk_resname}' (state: {dwk_key}) from installation")
                        break
            except Exception:  # noqa: BLE001
                # DWK variant not found, skip it
                pass
        
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Could not extract DWK walkmeshes: {e}")
    
    return door_walkmeshes


def _get_model_variations(model_name: str) -> list[str]:
    """Get list of model name variations to try when searching for resources.
    
    Some doors have models that don't exist, so we try various name formats.
    
    Args:
    ----
        model_name: Original model name
        
    Returns:
    -------
        List of model name variations (original case, lowercase, uppercase, normalized)
    """
    variations = [
        model_name,  # Original case
        model_name.lower(),  # Lowercase
        model_name.upper(),  # Uppercase
        model_name.lower().replace(".mdl", "").replace(".mdx", ""),  # Normalized lowercase
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    return [v for v in variations if v not in seen and not seen.add(v)]


def _load_mdl_with_variations(
    model_name: str,
    installation: Installation,
    logger: RobustLogger | None = None,
) -> tuple[MDL | None, bytes | None]:
    """Load MDL file trying multiple name variations.
    
    Args:
    ----
        model_name: Base model name to try
        installation: The game installation instance
        logger: Optional logger for debugging
        
    Returns:
    -------
        Tuple of (MDL object, MDL data bytes) if found, (None, None) otherwise
    """
    if logger is None:
        logger = RobustLogger()
    
    model_variations = _get_model_variations(model_name)
    
    # Try locations() first (more reliable, searches multiple locations)
    for model_var in model_variations:
        try:
            location_results = installation.locations(
                [ResourceIdentifier(resname=model_var, restype=ResourceType.MDL)],
                [
                    SearchLocation.OVERRIDE,
                    SearchLocation.MODULES,
                    SearchLocation.CHITIN,
                ],
            )
            for res_ident, loc_list in location_results.items():
                if loc_list:
                    loc = loc_list[0]
                    try:
                        with loc.filepath.open("rb") as f:
                            f.seek(loc.offset)
                            mdl_data = f.read(loc.size)
                        mdl = read_mdl(mdl_data)
                        return mdl, mdl_data
                    except Exception:  # noqa: BLE001
                        continue
        except Exception:  # noqa: BLE001
            continue
    
    # Fallback to resource() if locations() didn't work
    for model_var in model_variations:
        try:
            mdl_result = installation.resource(model_var, ResourceType.MDL)
            if mdl_result and mdl_result.data:
                mdl = read_mdl(mdl_result.data)
                return mdl, mdl_result.data
        except Exception:  # noqa: BLE001
            continue
    
    return None, None


def _get_door_dimensions_from_model(
    mdl: MDL,
    model_name: str,
    door_name: str | None = None,
    logger: RobustLogger | None = None,
) -> tuple[float, float] | None:
    """Calculate door dimensions from MDL bounding box.
    
    Doors are typically oriented along Y axis (width) and Z axis (height).
    X is typically depth/thickness.
    
    Args:
    ----
        mdl: MDL model object
        model_name: Model name for logging
        door_name: Optional door name for logging
        logger: Optional logger for debugging
        
    Returns:
    -------
        Tuple of (width, height) if calculated successfully, None otherwise
    """
    if logger is None:
        logger = RobustLogger()
    
    if not mdl or not mdl.root:
        return None
    
    bb_min = Vector3(1000000, 1000000, 1000000)
    bb_max = Vector3(-1000000, -1000000, -1000000)
    
    # Iterate through all nodes and their meshes
    nodes_to_check: list[MDLNode] = [mdl.root]
    mesh_count = 0
    while nodes_to_check:
        node: MDLNode = nodes_to_check.pop()
        if node.mesh:
            mesh_count += 1
            # Use mesh bounding box if available
            if node.mesh.bb_min and node.mesh.bb_max:
                bb_min.x = min(bb_min.x, node.mesh.bb_min.x)
                bb_min.y = min(bb_min.y, node.mesh.bb_min.y)
                bb_min.z = min(bb_min.z, node.mesh.bb_min.z)
                bb_max.x = max(bb_max.x, node.mesh.bb_max.x)
                bb_max.y = max(bb_max.y, node.mesh.bb_max.y)
                bb_max.z = max(bb_max.z, node.mesh.bb_max.z)
            # Fallback: calculate from vertex positions if bounding box not set
            elif node.mesh.vertex_positions:
                for vertex in node.mesh.vertex_positions:
                    bb_min.x = min(bb_min.x, vertex.x)
                    bb_min.y = min(bb_min.y, vertex.y)
                    bb_min.z = min(bb_min.z, vertex.z)
                    bb_max.x = max(bb_max.x, vertex.x)
                    bb_max.y = max(bb_max.y, vertex.y)
                    bb_max.z = max(bb_max.z, vertex.z)
        
        # Check child nodes
        nodes_to_check.extend(node.children)
    
    # Calculate dimensions from bounding box
    # Width is typically the Y dimension (horizontal when door is closed)
    # Height is typically the Z dimension (vertical)
    if bb_min.x < 1000000:  # Valid bounding box calculated
        width = abs(bb_max.y - bb_min.y)
        height = abs(bb_max.z - bb_min.z)
        
        # Only use calculated values if they're reasonable (not zero or extremely large)
        if 0.1 < width < 50.0 and 0.1 < height < 50.0:
            door_name_str = f"'{door_name}'" if door_name else ""
            logger.debug(
                f"[DOOR DEBUG] Extracted dimensions for door {door_name_str}: "
                f"{width:.2f} x {height:.2f} (from {mesh_count} meshes, model='{model_name}')"
            )
            return width, height
        else:
            door_name_str = f"'{door_name}'" if door_name else ""
            logger.warning(
                f"Calculated dimensions for door {door_name_str} out of range: "
                f"{width:.2f} x {height:.2f}, using defaults"
            )
    else:
        door_name_str = f"'{door_name}'" if door_name else ""
        logger.warning(
            f"Could not calculate bounding box for door {door_name_str} "
            f"(processed {mesh_count} meshes), using defaults"
        )
    
    return None


def _get_door_dimensions_from_texture(
    model_name: str,
    installation: Installation,
    door_name: str | None = None,
    logger: RobustLogger | None = None,
) -> tuple[float, float] | None:
    """Calculate door dimensions from door texture as fallback.
    
    Typical door textures are 256x512 or 512x1024 pixels.
    Typical door dimensions are 2-6 units wide, 2.5-3.5 units tall.
    Assuming 1 pixel ≈ 0.008-0.01 world units for doors.
    
    Args:
    ----
        model_name: Model name to get textures from
        installation: The game installation instance
        door_name: Optional door name for logging
        logger: Optional logger for debugging
        
    Returns:
    -------
        Tuple of (width, height) if calculated successfully, None otherwise
    """
    if logger is None:
        logger = RobustLogger()
    
    # Get textures from the model
    texture_names: list[str] = []
    model_variations = _get_model_variations(model_name)
    
    for model_var in model_variations:
        try:
            mdl_result = installation.resource(model_var, ResourceType.MDL)
            if mdl_result and mdl_result.data:
                texture_names = list(iterate_textures(mdl_result.data))
                break
        except Exception:  # noqa: BLE001
            continue
    
    if not texture_names:
        return None
    
    # Try to load the first texture
    texture_name = texture_names[0]
    texture_result = installation.resource(texture_name, ResourceType.TPC)
    if not texture_result:
        # Try TGA as fallback
        texture_result = installation.resource(texture_name, ResourceType.TGA)
    
    if not texture_result or not texture_result.data:
        return None
    
    # Read texture to get dimensions
    tex_width = 0
    tex_height = 0
    
    if texture_result.restype == ResourceType.TPC:
        tpc = read_tpc(texture_result.data)
        tex_width, tex_height = tpc.dimensions()
    elif texture_result.restype == ResourceType.TGA:
        # TGA header: width at offset 12, height at offset 14 (little-endian)
        if len(texture_result.data) >= 18:
            tex_width = int.from_bytes(texture_result.data[12:14], "little")
            tex_height = int.from_bytes(texture_result.data[14:16], "little")
    
    if tex_width <= 0 or tex_height <= 0:
        return None
    
    # Convert texture pixels to world units
    # Use aspect ratio to determine which dimension is width vs height
    # Doors are typically taller than wide, so height > width
    if tex_height > tex_width:
        # Portrait orientation - height is vertical, width is horizontal
        # Typical: 256x512 = 2.0x4.0, 512x1024 = 4.0x8.0
        # Scale factor: ~0.008-0.01 units per pixel
        scale_factor = 0.008  # Conservative estimate
        door_width = tex_width * scale_factor
        door_height = tex_height * scale_factor
    else:
        # Landscape or square - assume standard door proportions
        # Use height as the primary dimension
        scale_factor = 0.008
        door_height = tex_height * scale_factor
        # Width is typically 0.6-0.8x height for doors
        door_width = door_height * 0.7
    
    # Clamp to reasonable values
    door_width = max(1.0, min(door_width, 10.0))
    door_height = max(1.5, min(door_height, 10.0))
    
    return door_width, door_height


def get_door_dimensions(
    utd_data: bytes,
    installation: Installation,
    *,
    door_name: str | None = None,
    default_width: float = 2.0,
    default_height: float = 3.0,
    logger: RobustLogger | None = None,
) -> tuple[float, float]:
    """Get door dimensions (width, height) from model or texture.
    
    Tries to extract dimensions from MDL bounding box first, then falls back
    to texture-based estimation if model extraction fails.
    
    References:
    ----------
        vendor/reone/src/libs/game/object/door.cpp:66-67 - Door model lookup
        Door dimension calculation logic from kit.py extract_kit()
    
    Args:
    ----
        utd_data: UTD door data bytes
        installation: The game installation instance
        door_name: Optional door name for logging
        default_width: Default width if extraction fails (default: 2.0)
        default_height: Default height if extraction fails (default: 3.0)
        logger: Optional logger for debugging
        
    Returns:
    -------
        Tuple of (width, height) in world units
    """
    if logger is None:
        logger = RobustLogger()
    
    door_width = default_width
    door_height = default_height
    door_name_str = f"'{door_name}'" if door_name else ""
    
    try:
        utd = read_utd(utd_data)
        logger.debug(
            f"[DOOR DEBUG] Processing door {door_name_str} "
            f"(appearance_id={utd.appearance_id})"
        )
        
        # Get door model name from UTD using genericdoors.2da
        genericdoors_2da = load_genericdoors_2da(installation, logger)
        if not genericdoors_2da:
            logger.warning(
                f"Could not load genericdoors.2da for door {door_name_str}, using defaults"
            )
            return door_width, door_height
        
        model_name = get_model(utd, installation, genericdoors=genericdoors_2da)
        if not model_name:
            logger.warning(
                f"Could not get model name for door {door_name_str} "
                f"(appearance_id={utd.appearance_id}), using defaults"
            )
            return door_width, door_height
        
        # Try method 1: Get dimensions from model bounding box
        mdl, mdl_data = _load_mdl_with_variations(model_name, installation, logger)
        if mdl:
            dimensions = _get_door_dimensions_from_model(mdl, model_name, door_name, logger)
            if dimensions:
                door_width, door_height = dimensions
                return door_width, door_height
            else:
                logger.warning(
                    f"Could not extract dimensions from model '{model_name}' "
                    f"for door {door_name_str}, trying texture fallback"
                )
        else:
            model_variations = _get_model_variations(model_name)
            logger.warning(
                f"Could not load MDL '{model_name}' (tried variations: {model_variations}) "
                f"for door {door_name_str} "
                f"(appearance_id={utd.appearance_id}), trying texture fallback"
            )
        
        # Fallback: Get dimensions from door texture if model-based extraction failed
        dimensions = _get_door_dimensions_from_texture(model_name, installation, door_name, logger)
        if dimensions:
            door_width, door_height = dimensions
        else:
            logger.debug(
                f"[DOOR DEBUG] Door {door_name_str}: "
                f"Using default dimensions ({default_width} x {default_height}) - "
                f"model and texture extraction failed"
            )
    
    except Exception as e:  # noqa: BLE001
        logger.warning(
            f"Failed to get dimensions for door {door_name_str}: {e}"
        )
    
    logger.debug(
        f"[DOOR DEBUG] Final dimensions for door {door_name_str}: "
        f"width={door_width:.2f}, height={door_height:.2f}"
    )
    return door_width, door_height
