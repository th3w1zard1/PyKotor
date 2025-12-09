from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from pykotor.extract.file import ResourceIdentifier, ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.generics.utp import UTP, read_utp
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.module import Module
    from pykotor.extract.installation import Installation
    from pykotor.resource.type import SOURCE_TYPES


def get_model(
    utp: UTP,
    installation: Installation,
    *,
    placeables: TwoDA | SOURCE_TYPES | None = None,
) -> str:
    """Returns the model name for the given placeable.

    If no value is specified for the placeable parameters then it will be loaded from the given installation.

    Args:
    ----
        utp: UTP object of the placeable to lookup the model for.
        installation: The relevant installation.
        placeables: The placeables.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns the model name for the placeable.
    """
    if placeables is None:
        result: ResourceResult | None = installation.resource(resname="placeables", restype=ResourceType.TwoDA)
        if not result:
            raise ValueError("Resource 'placeables.2da' not found in the installation, cannot get UTP model.")
        placeables_2da = read_2da(result.data)
    elif not isinstance(placeables, TwoDA):
        placeables_2da = read_2da(placeables)

    return placeables_2da.get_row(utp.appearance_id).get_string("modelname")


def load_placeables_2da(
    installation: Installation,
    logger: RobustLogger | None = None,
) -> TwoDA | None:
    """Load placeables.2da from installation using priority order.
    
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
    
    placeables_2da: TwoDA | None = None
    
    # Try locations() first (more reliable, handles BIF files)
    try:
        location_results = installation.locations(
            [ResourceIdentifier(resname="placeables", restype=ResourceType.TwoDA)],
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
                    placeables_2da = read_2da(data)
                    break
    except Exception as e:  # noqa: BLE001
        logger.debug(f"locations() failed for placeables.2da: {e}")
    
    # Fallback: try resource() if locations() didn't work
    if placeables_2da is None:
        try:
            placeables_result: ResourceResult | None = installation.resource(resname="placeables", restype=ResourceType.TwoDA)
            if placeables_result and placeables_result.data:
                placeables_2da = read_2da(placeables_result.data)
        except Exception as e:  # noqa: BLE001
            logger.debug(f"resource() also failed for placeables.2da: {e}")
    
    return placeables_2da


def extract_placeable_walkmesh(
    utp_data: bytes,
    installation: Installation,
    *,
    module: Module | None = None,
    logger: RobustLogger | None = None,
) -> tuple[str, bytes] | None:
    """Extract placeable walkmesh (PWK file) for a placeable.
    
    Format: <modelname>.pwk
    
    References:
    ----------
        vendor/reone/src/libs/game/object/placeable.cpp:73 - PWK extraction (modelname.pwk)
        vendor/reone/src/libs/game/object/placeable.cpp:59-60 - Placeable model lookup
        vendor/KotOR.js/src/module/ModulePlaceable.ts:684 - PWK loading
    
    Args:
    ----
        utp_data: UTP placeable data bytes
        installation: The game installation instance
        module: Optional Module instance to search for PWK file in module resources first
        logger: Optional logger for debugging
        
    Returns:
    -------
        Tuple of (model_name, pwk_data) if found, None otherwise
    """
    if logger is None:
        logger = RobustLogger()
    
    try:
        utp = read_utp(utp_data)
        
        # Get placeable model name from UTP using placeables.2da
        placeables_2da = load_placeables_2da(installation, logger)
        if not placeables_2da:
            logger.warning("Could not load placeables.2da, cannot extract placeable walkmesh")
            return None
        
        placeable_model_name = get_model(utp, installation, placeables=placeables_2da)
        if not placeable_model_name:
            logger.warning(f"Could not get model name for placeable (appearance_id={utp.appearance_id})")
            return None
        
        # Try to extract PWK file: modelname.pwk
        try:
            # Try to find PWK in module resources first (if module provided)
            if module is not None:
                pwk_resource = module.resource(resname=placeable_model_name, restype=ResourceType.PWK)
                if pwk_resource is not None:
                    pwk_data = pwk_resource.data()
                    if pwk_data is not None:
                        logger.info(f"Found PWK '{placeable_model_name}' from module")
                        return placeable_model_name, pwk_data
            
            # Try installation locations
            pwk_locations = installation.locations(
                [ResourceIdentifier(resname=placeable_model_name, restype=ResourceType.PWK)],
                [
                    SearchLocation.OVERRIDE,
                    SearchLocation.MODULES,
                    SearchLocation.CHITIN,
                ],
            )
            for pwk_ident, pwk_loc_list in pwk_locations.items():
                if pwk_loc_list:
                    pwk_loc = pwk_loc_list[0]
                    with pwk_loc.filepath.open("rb") as f:
                        f.seek(pwk_loc.offset)
                        pwk_data = f.read(pwk_loc.size)
                    logger.debug(f"Found PWK '{placeable_model_name}' from installation")
                    return placeable_model_name, pwk_data
        
        except Exception:  # noqa: BLE001
            logger.debug(f"PWK '{placeable_model_name}' not found, skip it", exc_info=True)
    except Exception:  # noqa: BLE001
        logger.debug(f"Could not extract PWK walkmesh for '{placeable_model_name}'", exc_info=True)
    return None
