"""Archive utility functions for extracting, listing, and creating archives.

This module provides reusable, abstract functions for working with KOTOR archive formats
(KEY/BIF, RIM, ERF/MOD/SAV/HAK). These functions are tool-agnostic and can be used
by any application that needs to work with archives.

References:
----------
    vendor/reone/src/libs/tools/legacy/keybif.cpp:78-112 - KEY/BIF extraction
    vendor/xoreos-tools/src/unkeybif.cpp - KEY/BIF extraction tool
    vendor/xoreos-tools/src/unerf.cpp - ERF extraction tool
    vendor/xoreos-tools/src/unrim.cpp - RIM extraction tool
    vendor/xoreos-tools/src/archives/util.h - Archive utilities interface
"""
from __future__ import annotations

import fnmatch

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from pykotor.resource.formats.bif.bif_auto import read_bif
from pykotor.resource.formats.erf.erf_auto import read_erf
from pykotor.resource.formats.key.key_auto import read_key
from pykotor.resource.formats.rim.rim_auto import read_rim

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pykotor.resource.bioware_archive import ArchiveResource


def matches_filter(text: str, pattern: str) -> bool:
    """Check if text matches filter pattern (supports wildcards).

    Args:
    ----
        text: Text to check
        pattern: Filter pattern (supports * and ? wildcards)

    Returns:
    -------
        True if text matches pattern, False otherwise
    """
    if "*" in pattern or "?" in pattern:
        return fnmatch.fnmatch(text.lower(), pattern.lower())
    return pattern.lower() in text.lower()


def extract_erf(
    erf_path: Path,
    output_dir: Path,
    *,
    filter_pattern: str | None = None,
    resource_filter: Callable[[ArchiveResource], bool] | None = None,
) -> Iterator[tuple[ArchiveResource, Path]]:
    """Extract resources from an ERF/MOD/SAV/HAK archive.

    This is a generator that yields (resource, output_path) tuples for each resource
    that matches the filter. The caller is responsible for writing the resource data.

    Args:
    ----
        erf_path: Path to the ERF archive file
        output_dir: Directory to extract resources to
        filter_pattern: Optional wildcard pattern to filter resources by name
        resource_filter: Optional callable to filter resources (takes precedence over filter_pattern)

    Yields:
    ------
        Tuple of (resource, output_path) for each matching resource

    References:
    ----------
        vendor/xoreos-tools/src/unerf.cpp
        vendor/reone/src/libs/resource/format/erfreader.cpp
    """
    erf_data = read_erf(erf_path)

    for resource in erf_data:
        resref = resource.resref.get() if resource.resref else "unknown"

        # Apply filters
        if resource_filter is not None:
            if not resource_filter(resource):
                continue
        elif filter_pattern and not matches_filter(resref, filter_pattern):
            continue

        ext = resource.restype.extension if resource.restype else "bin"
        output_file = output_dir / f"{resref}.{ext}"

        yield resource, output_file


def extract_rim(
    rim_path: Path,
    output_dir: Path,
    *,
    filter_pattern: str | None = None,
    resource_filter: Callable[[ArchiveResource], bool] | None = None,
) -> Iterator[tuple[ArchiveResource, Path]]:
    """Extract resources from a RIM archive.

    This is a generator that yields (resource, output_path) tuples for each resource
    that matches the filter. The caller is responsible for writing the resource data.

    Args:
    ----
        rim_path: Path to the RIM archive file
        output_dir: Directory to extract resources to
        filter_pattern: Optional wildcard pattern to filter resources by name
        resource_filter: Optional callable to filter resources (takes precedence over filter_pattern)

    Yields:
    ------
        Tuple of (resource, output_path) for each matching resource

    References:
    ----------
        vendor/xoreos-tools/src/unrim.cpp
        vendor/reone/src/libs/resource/format/rimreader.cpp
    """
    rim_data = read_rim(rim_path)

    for resource in rim_data:
        resref = resource.resref.get() if resource.resref else "unknown"

        # Apply filters
        if resource_filter is not None:
            if not resource_filter(resource):
                continue
        elif filter_pattern and not matches_filter(resref, filter_pattern):
            continue

        ext = resource.restype.extension if resource.restype else "bin"
        output_file = output_dir / f"{resref}.{ext}"

        yield resource, output_file


def extract_bif(
    bif_path: Path,
    output_dir: Path,
    *,
    key_path: Path | None = None,
    filter_pattern: str | None = None,
    resource_filter: Callable[[ArchiveResource], bool] | None = None,
) -> Iterator[tuple[ArchiveResource, Path]]:
    """Extract resources from a BIF file.

    This is a generator that yields (resource, output_path) tuples for each resource
    that matches the filter. The caller is responsible for writing the resource data.

    Args:
    ----
        bif_path: Path to the BIF file
        output_dir: Directory to extract resources to
        key_path: Optional path to KEY file for resource name resolution
        filter_pattern: Optional wildcard pattern to filter resources by name
        resource_filter: Optional callable to filter resources (takes precedence over filter_pattern)

    Yields:
    ------
        Tuple of (resource, output_path) for each matching resource

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/keybif.cpp:78-112
    """
    key_source = key_path if key_path and key_path.exists() else None

    with bif_path.open("rb") as bif_file:
        bif_data = read_bif(bif_file, key_source=key_source)

    for i, resource in enumerate(bif_data):
        resref = resource.resref.get() if resource.resref else f"resource_{i:05d}"

        # Apply filters
        if resource_filter is not None:
            if not resource_filter(resource):
                continue
        elif filter_pattern and not matches_filter(resref, filter_pattern):
            continue

        ext = resource.restype.extension if resource.restype else "bin"
        output_file = output_dir / f"{resref}.{ext}"

        yield resource, output_file


def extract_key_bif(
    key_path: Path,
    output_dir: Path,
    *,
    bif_search_dir: Path | None = None,
    filter_pattern: str | None = None,
    resource_filter: Callable[[ArchiveResource], bool] | None = None,
) -> Iterator[tuple[ArchiveResource, Path, Path]]:
    """Extract resources from KEY/BIF archives.

    This is a generator that yields (resource, output_path, bif_path) tuples for each resource
    that matches the filter. The caller is responsible for writing the resource data.

    Args:
    ----
        key_path: Path to the KEY file
        output_dir: Base directory to extract resources to (BIF files create subdirectories)
        bif_search_dir: Directory to search for BIF files (defaults to key_path.parent)
        filter_pattern: Optional wildcard pattern to filter resources by name
        resource_filter: Optional callable to filter resources (takes precedence over filter_pattern)

    Yields:
    ------
        Tuple of (resource, output_path, bif_path) for each matching resource

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/keybif.cpp:78-112
        vendor/xoreos-tools/src/unkeybif.cpp
    """
    with key_path.open("rb") as key_file:
        key_data = read_key(key_file)

    # Find BIF files
    search_dir = bif_search_dir if bif_search_dir else key_path.parent
    bif_files: dict[int, Path] = {}

    for bif_entry in key_data.bif_entries:
        bif_name = bif_entry.filename
        bif_path = search_dir / bif_name

        if not bif_path.exists():
            # Try case-insensitive search
            for candidate in search_dir.iterdir():
                if candidate.name.lower() == bif_name.lower():
                    bif_path = candidate
                    break
            else:
                continue  # Skip missing BIF files

        # Store BIF path by its index
        bif_index = key_data.bif_entries.index(bif_entry)
        bif_files[bif_index] = bif_path

    # Extract from each BIF
    for bif_index, bif_path in bif_files.items():
        with bif_path.open("rb") as bif_file:
            bif_data = read_bif(bif_file, key_source=key_path)

        for i, resource in enumerate(bif_data):
            resref = resource.resref.get() if resource.resref else f"resource_{i:05d}"

            # Apply filters
            if resource_filter is not None:
                if not resource_filter(resource):
                    continue
            elif filter_pattern and not matches_filter(resref, filter_pattern):
                continue

            ext = resource.restype.extension if resource.restype else "bin"
            output_file = output_dir / bif_path.stem / f"{resref}.{ext}"

            yield resource, output_file, bif_path


def list_erf(erf_path: Path) -> Iterator[ArchiveResource]:
    """List all resources in an ERF/MOD/SAV/HAK archive.

    Args:
    ----
        erf_path: Path to the ERF archive file

    Yields:
    ------
        ArchiveResource objects for each resource in the archive
    """
    erf_data = read_erf(erf_path)
    yield from erf_data


def list_rim(rim_path: Path) -> Iterator[ArchiveResource]:
    """List all resources in a RIM archive.

    Args:
    ----
        rim_path: Path to the RIM archive file

    Yields:
    ------
        ArchiveResource objects for each resource in the archive
    """
    rim_data = read_rim(rim_path)
    yield from rim_data


def list_bif(
    bif_path: Path,
    *,
    key_path: Path | None = None,
) -> Iterator[ArchiveResource]:
    """List all resources in a BIF file.

    Args:
    ----
        bif_path: Path to the BIF file
        key_path: Optional path to KEY file for resource name resolution

    Yields:
    ------
        ArchiveResource objects for each resource in the archive
    """
    key_source = key_path if key_path and key_path.exists() else None

    with bif_path.open("rb") as bif_file:
        bif_data = read_bif(bif_file, key_source=key_source)

    yield from bif_data


def list_key(key_path: Path) -> tuple[list[str], list[tuple[str, str, int, int]]]:
    """List BIF files and resources in a KEY file.

    Args:
    ----
        key_path: Path to the KEY file

    Returns:
    -------
        Tuple of (bif_files, resources) where:
        - bif_files: List of BIF filenames
        - resources: List of (resref, restype_ext, bif_index, res_index) tuples
    """
    with key_path.open("rb") as key_file:
        key_data = read_key(key_file)

    bif_files = [bif_entry.filename for bif_entry in key_data.bif_entries]

    resources = []
    for key_entry in key_data.key_entries:
        resref = str(key_entry.resref)
        restype_ext = key_entry.restype.extension if key_entry.restype else "?"
        resources.append((resref, restype_ext, key_entry.bif_index, key_entry.res_index))

    return bif_files, resources


def create_erf_from_directory(
    input_dir: Path,
    output_path: Path,
    *,
    erf_type: str = "ERF",  # "ERF", "MOD", "SAV"
    file_filter: str | None = None,
) -> None:
    """Create an ERF/MOD/SAV archive from a directory of files.

    Args:
    ----
        input_dir: Directory containing files to pack
        output_path: Path to write the output ERF file
        erf_type: Type of ERF to create ("ERF", "MOD", or "SAV")
        file_filter: Optional wildcard filter for files to include

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/erf.cpp:83-130 - ERF creation from directory
        vendor/xoreos-tools/src/erf.cpp:49-96 - ERF packing
    """
    from pykotor.common.misc import ResRef
    from pykotor.resource.formats.erf.erf_auto import write_erf
    from pykotor.resource.formats.erf.erf_data import ERF, ERFType
    from pykotor.resource.type import ResourceType

    # Map string type to ERFType enum
    type_map = {
        "ERF": ERFType.ERF,
        "MOD": ERFType.MOD,
        "SAV": ERFType.MOD,  # SAV uses MOD signature
    }
    erf_enum_type = type_map.get(erf_type.upper(), ERFType.ERF)

    erf = ERF(erf_enum_type)
    if erf_type.upper() == "SAV":
        erf.is_save = True

    # Collect files from directory
    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue

        # Apply filter if specified
        if file_filter and not matches_filter(file_path.name, file_filter):
            continue

        # Parse filename to get resref and extension
        # Handle both "resref.ext" and "resref.123.ext" formats
        stem = file_path.stem
        ext = file_path.suffix.lstrip(".")

        try:
            restype = ResourceType.from_extension(ext)
        except ValueError:
            continue  # Skip unknown file types

        # Handle files with embedded type in stem (e.g., "model.123.mdl")
        if "." in stem:
            parts = stem.split(".")
            # Check if last part is numeric (resource ID)
            if parts[-1].isdigit():
                resref = ".".join(parts[:-1])
            else:
                resref = stem
        else:
            resref = stem

        # Read file data and add to ERF
        file_data = file_path.read_bytes()
        erf.set_data(ResRef(resref), restype, file_data)

    # Write ERF archive
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_erf(erf, output_path)


def create_rim_from_directory(
    input_dir: Path,
    output_path: Path,
    *,
    file_filter: str | None = None,
) -> None:
    """Create a RIM archive from a directory of files.

    Args:
    ----
        input_dir: Directory containing files to pack
        output_path: Path to write the output RIM file
        file_filter: Optional wildcard filter for files to include

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/rim.cpp:83-121 - RIM creation from directory
        vendor/xoreos-tools/src/rim.cpp:43-84 - RIM packing
    """
    from pykotor.common.misc import ResRef
    from pykotor.resource.formats.rim.rim_auto import write_rim
    from pykotor.resource.formats.rim.rim_data import RIM
    from pykotor.resource.type import ResourceType

    rim = RIM()

    # Collect files from directory
    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue

        # Apply filter if specified
        if file_filter and not matches_filter(file_path.name, file_filter):
            continue

        # Parse filename to get resref and extension
        stem = file_path.stem
        ext = file_path.suffix.lstrip(".")

        try:
            restype = ResourceType.from_extension(ext)
        except ValueError:
            continue  # Skip unknown file types

        # Handle files with embedded type in stem (e.g., "model.123.mdl")
        if "." in stem:
            parts = stem.split(".")
            if parts[-1].isdigit():
                resref = ".".join(parts[:-1])
            else:
                resref = stem
        else:
            resref = stem

        # Read file data and add to RIM
        file_data = file_path.read_bytes()
        rim.set_data(ResRef(resref), restype, file_data)

    # Write RIM archive
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rim(rim, output_path)


def search_in_erf(
    erf_path: Path,
    pattern: str,
    *,
    case_sensitive: bool = False,
    search_content: bool = False,
) -> Iterator[tuple[str, str]]:
    """Search for resources in an ERF archive by name or content.

    Args:
    ----
        erf_path: Path to the ERF archive
        pattern: Search pattern (supports wildcards for name search)
        case_sensitive: Whether search is case-sensitive
        search_content: If True, search in resource content; if False, search in resource names only

    Yields:
    ------
        Tuple of (resref, restype) for matching resources

    References:
    ----------
        vendor/neverwinter.nim/nwn_resman_grep - Resource grep utility
        vendor/xoreos-tools/src/ - Archive search utilities
    """
    import re

    erf_data = read_erf(erf_path)

    # Compile pattern
    if not case_sensitive:
        pattern = pattern.lower()
    if "*" in pattern or "?" in pattern:
        # Use fnmatch
        use_fnmatch = True
    else:
        use_fnmatch = False
        regex_pattern = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)

    for resource in erf_data:
        resref = resource.resref.get() if resource.resref else "unknown"
        restype = resource.restype.extension if resource.restype else "bin"

        # Search in name
        name_to_search = resref if case_sensitive else resref.lower()
        if use_fnmatch:
            if fnmatch.fnmatch(name_to_search, pattern):
                yield resref, restype
        elif regex_pattern.search(name_to_search):
            yield resref, restype

        # Search in content if requested
        if search_content:
            try:
                content = resource.data.decode("utf-8", errors="ignore")
                content_to_search = content if case_sensitive else content.lower()
                if use_fnmatch:
                    if pattern in content_to_search:
                        yield resref, restype
                elif regex_pattern.search(content_to_search):
                    yield resref, restype
            except Exception:
                pass  # Skip binary resources that can't be decoded


def search_in_rim(
    rim_path: Path,
    pattern: str,
    *,
    case_sensitive: bool = False,
    search_content: bool = False,
) -> Iterator[tuple[str, str]]:
    """Search for resources in a RIM archive by name or content.

    Args:
    ----
        rim_path: Path to the RIM archive
        pattern: Search pattern (supports wildcards for name search)
        case_sensitive: Whether search is case-sensitive
        search_content: If True, search in resource content; if False, search in resource names only

    Yields:
    ------
        Tuple of (resref, restype) for matching resources
    """
    import re

    rim_data = read_rim(rim_path)

    # Compile pattern
    if not case_sensitive:
        pattern = pattern.lower()
    if "*" in pattern or "?" in pattern:
        use_fnmatch = True
    else:
        use_fnmatch = False
        regex_pattern = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)

    for resource in rim_data:
        resref = resource.resref.get() if resource.resref else "unknown"
        restype = resource.restype.extension if resource.restype else "bin"

        # Search in name
        name_to_search = resref if case_sensitive else resref.lower()
        if use_fnmatch:
            if fnmatch.fnmatch(name_to_search, pattern):
                yield resref, restype
        elif regex_pattern.search(name_to_search):
            yield resref, restype

        # Search in content if requested
        if search_content:
            try:
                content = resource.data.decode("utf-8", errors="ignore")
                content_to_search = content if case_sensitive else content.lower()
                if use_fnmatch:
                    if pattern in content_to_search:
                        yield resref, restype
                elif regex_pattern.search(content_to_search):
                    yield resref, restype
            except Exception:
                pass  # Skip binary resources that can't be decoded


def get_resource_from_archive(
    archive_path: Path,
    resref: str,
    restype: str | None = None,
) -> bytes | None:
    """Get a resource's data from an archive.

    Args:
    ----
        archive_path: Path to the archive (ERF, RIM, KEY/BIF)
        resref: Resource reference name
        restype: Resource type extension (optional, will try to detect from archive)

    Returns:
    -------
        Resource data as bytes, or None if not found

    References:
    ----------
        vendor/neverwinter.nim/nwn_resman_cat - Resource cat utility
        Tools/HolocronToolset/src/toolset/utils/misc.py:221-262 - get_resource_from_file
    """
    from pykotor.resource.type import ResourceType

    archive_path = Path(archive_path)
    suffix = archive_path.suffix.lower()

    # Determine resource type
    if restype:
        try:
            resource_type = ResourceType.from_extension(restype)
        except ValueError:
            return None
    else:
        # Try to infer from archive listing
        resource_type = None

    # Read archive
    if suffix in (".erf", ".mod", ".sav", ".hak"):
        erf_data = read_erf(archive_path)
        if resource_type:
            return erf_data.get(resref, resource_type)
        # Try common types if not specified
        for common_type in [ResourceType.NSS, ResourceType.DLG, ResourceType.UTC, ResourceType.UTI]:
            result = erf_data.get(resref, common_type)
            if result is not None:
                return result
    elif suffix == ".rim":
        rim_data = read_rim(archive_path)
        if resource_type:
            return rim_data.get(resref, resource_type)
        # Try common types if not specified
        for common_type in [ResourceType.NSS, ResourceType.DLG, ResourceType.UTC, ResourceType.UTI]:
            result = rim_data.get(resref, common_type)
            if result is not None:
                return result

    return None


def create_key_from_directory(
    input_dir: Path,
    bif_dir: Path,
    output_path: Path,
    *,
    file_filter: str | None = None,
) -> None:
    """Create a KEY file from a directory containing BIF files.

    Args:
    ----
        input_dir: Directory containing BIF files (or subdirectories with BIFs)
        bif_dir: Directory where BIF files are/will be located (relative paths in KEY)
        output_path: Path to write the output KEY file
        file_filter: Optional wildcard filter for BIF files to include

    References:
    ----------
        vendor/xoreos-tools/src/keybif.cpp - KEY/BIF creation tool
        vendor/reone/src/libs/resource/format/keywriter.cpp - KEY writing
        Libraries/PyKotor/src/pykotor/extract/keywriter.py:44-143 - KEYWriter class
    """
    from pykotor.common.misc import ResRef
    from pykotor.resource.formats.bif.bif_auto import read_bif
    from pykotor.resource.formats.key.key_auto import write_key
    from pykotor.resource.formats.key.key_data import KEY, BifEntry, KeyEntry
    from pykotor.resource.type import ResourceType

    key = KEY()

    # Collect all BIF files
    bif_files: list[Path] = []
    for file_path in input_dir.rglob("*.bif"):
        if not file_path.is_file():
            continue

        # Apply filter if specified
        if file_filter and not matches_filter(file_path.name, file_filter):
            continue

        bif_files.append(file_path)

    # Process each BIF file
    for bif_path in bif_files:
        # Calculate relative path from bif_dir
        try:
            rel_path = bif_path.relative_to(bif_dir)
            bif_filename = str(rel_path).replace("\\", "/")
        except ValueError:
            # If not relative, use just the filename
            bif_filename = bif_path.name

        bif_size = bif_path.stat().st_size

        # Read BIF to get resources
        with bif_path.open("rb") as bif_file:
            bif_data = read_bif(bif_file)

        # Create BIF entry
        bif_entry = BifEntry(bif_filename, bif_size)
        bif_index = len(key.bif_entries)
        key.bif_entries.append(bif_entry)

        # Add resource entries
        for i, resource in enumerate(bif_data):
            resref = resource.resref.get() if resource.resref else f"resource_{i:05d}"
            restype = resource.restype if resource.restype else ResourceType.INVALID

            # Resource ID: top 12 bits = BIF index, bottom 20 bits = resource index
            resource_id = (bif_index << 20) | i

            key_entry = KeyEntry(ResRef(resref), restype, resource_id)
            key.key_entries.append(key_entry)

    # Build lookup tables and write KEY
    key.build_lookup_tables()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_key(key, output_path)

