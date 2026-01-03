from __future__ import annotations

from pathlib import Path

from loggerplus import RobustLogger


def is_save_corrupted(save_path: Path) -> bool:
    """Check if a save game is corrupted using a lightweight check.

    This method performs a quick check for EventQueue corruption without
    loading the entire save structure into memory.

    Args:
    ----
        save_path: Path to the save game folder

    Returns:
    -------
        True if the save is corrupted, False otherwise
    """
    try:
        # Use lightweight corruption check that doesn't load the entire save
        return _check_save_corruption_lightweight(save_path)
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        # If we can't check the save, assume it's not corrupted (safer than false positives)
        RobustLogger().debug(f"Failed to check corruption for save at '{save_path}'")
        return False


def _check_save_corruption_lightweight(save_path: Path) -> bool:
    """Lightweight corruption check that doesn't fully parse saves.

    Only reads the SAVEGAME.sav ERF and checks for EventQueue entries
    in cached module IFOs without parsing everything else.

    Args:
    ----
        save_path: Path to the save game folder

    Returns:
    -------
        True if corrupted (has EventQueue entries), False otherwise
    """
    from pykotor.resource.formats.erf.erf_auto import read_erf
    from pykotor.resource.formats.gff.gff_auto import read_gff
    from pykotor.resource.type import ResourceType

    savegame_sav = save_path / "SAVEGAME.sav"
    if not savegame_sav.exists():
        return False

    try:
        # Read the outer ERF (SAVEGAME.sav)
        outer_erf = read_erf(savegame_sav)

        # Check each .sav resource (cached modules) for EventQueue corruption
        for resource in outer_erf:
            if resource.restype is not ResourceType.SAV:
                continue

            # Read the nested module ERF
            try:
                inner_erf = read_erf(resource.data)

                # Look for module.ifo in this cached module
                for inner_resource in inner_erf:
                    if str(inner_resource.resref).lower() == "module" and inner_resource.restype is ResourceType.IFO:
                        # Check for EventQueue
                        ifo_gff = read_gff(inner_resource.data)
                        if ifo_gff.root.exists("EventQueue"):
                            event_queue = ifo_gff.root.get_list("EventQueue")
                            if event_queue and len(event_queue) > 0:
                                return True  # Corrupted!
                        break  # Only one module.ifo per cached module
            except Exception:  # noqa: BLE001
                continue  # Skip malformed nested ERFs

        return False  # No corruption found
    except Exception:  # noqa: BLE001
        return False  # If we can't parse, assume not corrupted


def fix_save_corruption(save_path: Path) -> bool:
    """Fix EventQueue corruption in a save by clearing EventQueues from cached modules.

    This method clears the EventQueue list from all cached module IFOs in the save,
    which is a common fix for save corruption issues.

    Args:
    ----
        save_path: Path to the save game folder

    Returns:
    -------
        True if any corruption was fixed, False if no corruption was found or fix failed
    """
    from pykotor.resource.formats.erf.erf_auto import read_erf, write_erf
    from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
    from pykotor.resource.formats.gff.gff_data import GFFList
    from pykotor.resource.type import ResourceType

    savegame_sav = save_path / "SAVEGAME.sav"
    if not savegame_sav.exists():
        return False

    try:
        # Read the outer ERF (SAVEGAME.sav)
        outer_erf = read_erf(savegame_sav)
        any_fixed = False

        # Process each .sav resource (cached modules)
        for resource in outer_erf:
            if resource.restype is not ResourceType.SAV:
                continue

            try:
                inner_erf = read_erf(resource.data)
                inner_modified = False

                # Look for module.ifo in this cached module
                for inner_resource in inner_erf:
                    if str(inner_resource.resref).lower() == "module" and inner_resource.restype is ResourceType.IFO:
                        # Check and clear EventQueue
                        ifo_gff = read_gff(inner_resource.data)
                        if ifo_gff.root.exists("EventQueue"):
                            event_queue = ifo_gff.root.get_list("EventQueue")
                            if event_queue and len(event_queue) > 0:
                                # Clear the EventQueue
                                ifo_gff.root.set_list("EventQueue", GFFList())
                                # Update the resource data
                                inner_erf.set_data(str(inner_resource.resref), inner_resource.restype, bytes_gff(ifo_gff, ResourceType.IFO))
                                inner_modified = True
                                any_fixed = True
                        break

                if inner_modified:
                    # Update the outer ERF with the modified inner ERF
                    from pykotor.resource.formats.erf.erf_auto import bytes_erf

                    outer_erf.set_data(str(resource.resref), resource.restype, bytes_erf(inner_erf, ResourceType.SAV))

            except Exception as e:  # noqa: BLE001
                RobustLogger().warning(f"Failed to process cached module {resource.resref}: {e}")
                continue

        if any_fixed:
            # Write the fixed outer ERF back to disk
            write_erf(outer_erf, savegame_sav, ResourceType.SAV)
            RobustLogger().info(f"Fixed EventQueue corruption in save: {save_path.name}")
            return True

        return False  # No corruption to fix

    except Exception as e:  # noqa: BLE001
        RobustLogger().exception(f"Failed to fix corruption for save at '{save_path}': {e}")
        return False
