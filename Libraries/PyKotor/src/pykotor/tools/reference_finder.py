"""Comprehensive reference finding utilities for KotOR resources.

This module provides functions to find references to scripts, tags, resrefs, conversations,
and other values across GFF files, NCS bytecode, and 2DA files in a KotOR installation.

Based on the functionality of the KotOR findrefs utility, integrated into PyKotor.
"""

from __future__ import annotations

import fnmatch
import re

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource
from pykotor.resource.formats.gff import GFF, GFFFieldType, GFFList, GFFStruct, read_gff
from pykotor.resource.formats.ncs import NCSByteCode, NCSInstructionQualifier
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.extract.installation import Installation


@dataclass(frozen=True)
class ReferenceSearchResult:
    """Result of a reference search operation.

    Attributes:
    ----------
        file_resource: The FileResource where the reference was found
        field_path: GFF field path where match was found (e.g., "ScriptHeartbeat", "ItemList[0].InventoryRes")
        matched_value: The value that was matched
        file_type: The file type abbreviation (e.g., "UTC", "UTD", "NCS")
        byte_offset: Optional byte offset for NCS matches
    """

    file_resource: FileResource
    field_path: str
    matched_value: str
    file_type: str
    byte_offset: int | None = None


def find_script_references(
    installation: Installation,
    script_resref: str,
    *,
    partial_match: bool = False,
    case_sensitive: bool = False,
    file_pattern: str | None = None,
    file_types: set[str] | None = None,
    logger: Callable[[str], None] | None = None,
) -> list[ReferenceSearchResult]:
    """Find all references to a script (NCS/NSS) resref in GFF files and NCS bytecode.

    Args:
    ----
        installation: The installation to search
        script_resref: The script resref to search for (without extension)
        partial_match: If True, allow partial matches (e.g., "test" matches "testscript")
        case_sensitive: If True, perform case-sensitive matching
        file_pattern: Optional file pattern to filter results (e.g., "*.mod", "*_s.rim")
        file_types: Optional set of file type abbreviations to search (e.g., {"UTC", "UTD", "ARE"})
        logger: Optional logging function

    Returns:
    -------
        List of ReferenceSearchResult objects
    """
    return find_resref_references(
        installation=installation,
        resref=script_resref,
        field_types={GFFFieldType.ResRef},
        search_ncs=True,
        partial_match=partial_match,
        case_sensitive=case_sensitive,
        file_pattern=file_pattern,
        file_types=file_types,
        logger=logger,
    )


def find_tag_references(
    installation: Installation,
    tag: str,
    *,
    partial_match: bool = False,
    case_sensitive: bool = False,
    file_pattern: str | None = None,
    file_types: set[str] | None = None,
    logger: Callable[[str], None] | None = None,
) -> list[ReferenceSearchResult]:
    """Find all references to a tag in GFF files.

    Args:
    ----
        installation: The installation to search
        tag: The tag value to search for
        partial_match: If True, allow partial matches
        case_sensitive: If True, perform case-sensitive matching
        file_pattern: Optional file pattern to filter results
        file_types: Optional set of file type abbreviations to search
        logger: Optional logging function

    Returns:
    -------
        List of ReferenceSearchResult objects
    """
    return find_field_value_references(
        installation=installation,
        search_value=tag,
        field_names={"Tag"},
        field_types={GFFFieldType.String},
        partial_match=partial_match,
        case_sensitive=case_sensitive,
        file_pattern=file_pattern,
        file_types=file_types,
        logger=logger,
    )


def find_template_resref_references(
    installation: Installation,
    template_resref: str,
    *,
    partial_match: bool = False,
    case_sensitive: bool = False,
    file_pattern: str | None = None,
    file_types: set[str] | None = None,
    logger: Callable[[str], None] | None = None,
) -> list[ReferenceSearchResult]:
    """Find all references to a TemplateResRef in GFF files.

    Searches for TemplateResRef fields and InventoryRes fields within ItemList structures
    (for UTC, UTP, UTM files).

    Args:
    ----
        installation: The installation to search
        template_resref: The template resref to search for
        partial_match: If True, allow partial matches
        case_sensitive: If True, perform case-sensitive matching
        file_pattern: Optional file pattern to filter results
        file_types: Optional set of file type abbreviations to search
        logger: Optional logging function

    Returns:
    -------
        List of ReferenceSearchResult objects
    """
    # Include InventoryRes to search ItemList structures in UTC/UTP/UTM
    return find_resref_references(
        installation=installation,
        resref=template_resref,
        field_names={"TemplateResRef", "InventoryRes"},
        field_types={GFFFieldType.ResRef},
        partial_match=partial_match,
        case_sensitive=case_sensitive,
        file_pattern=file_pattern,
        file_types=file_types,
        logger=logger,
    )


def find_conversation_references(
    installation: Installation,
    conversation_resref: str,
    *,
    partial_match: bool = False,
    case_sensitive: bool = False,
    file_pattern: str | None = None,
    file_types: set[str] | None = None,
    logger: Callable[[str], None] | None = None,
) -> list[ReferenceSearchResult]:
    """Find all references to a conversation (DLG) resref in GFF files.

    Args:
    ----
        installation: The installation to search
        conversation_resref: The conversation resref to search for
        partial_match: If True, allow partial matches
        case_sensitive: If True, perform case-sensitive matching
        file_pattern: Optional file pattern to filter results
        file_types: Optional set of file type abbreviations to search
        logger: Optional logging function

    Returns:
    -------
        List of ReferenceSearchResult objects
    """
    return find_resref_references(
        installation=installation,
        resref=conversation_resref,
        field_names={"Conversation"},
        field_types={GFFFieldType.ResRef},
        partial_match=partial_match,
        case_sensitive=case_sensitive,
        file_pattern=file_pattern,
        file_types=file_types,
        logger=logger,
    )


def find_resref_references(
    installation: Installation,
    resref: str,
    *,
    field_names: set[str] | None = None,
    field_types: set[GFFFieldType] | None = None,
    search_ncs: bool = False,
    partial_match: bool = False,
    case_sensitive: bool = False,
    file_pattern: str | None = None,
    file_types: set[str] | None = None,
    logger: Callable[[str], None] | None = None,
) -> list[ReferenceSearchResult]:
    """Find all references to a ResRef in GFF files and optionally NCS bytecode.

    Args:
    ----
        installation: The installation to search
        resref: The resref to search for
        field_names: Optional set of specific field names to search (e.g., {"ScriptHeartbeat", "Conversation"})
        field_types: Set of GFF field types to search (default: {GFFFieldType.ResRef})
        search_ncs: If True, also search NCS bytecode for string constants
        partial_match: If True, allow partial matches
        case_sensitive: If True, perform case-sensitive matching
        file_pattern: Optional file pattern to filter results
        file_types: Optional set of file type abbreviations to search
        logger: Optional logging function

    Returns:
    -------
        List of ReferenceSearchResult objects
    """
    if field_types is None:
        field_types = {GFFFieldType.ResRef}

    # Build search pattern
    search_pattern = _build_search_pattern(resref, partial_match, case_sensitive)

    results: list[ReferenceSearchResult] = []

    exclude_types = {ResourceType.NCS} if search_ncs else None

    # Cache parsed GFF files by FileResource to avoid re-parsing the same file
    # This handles cases where the same resource appears multiple times in the installation iterator
    # (e.g., in both override and modules). This is an O(n) -> O(1) optimization for parsing.
    gff_cache: dict[FileResource, GFF | None] = {}

    # Search GFF files
    for resource in installation:
        if not _should_search_resource(resource, file_pattern, file_types, exclude_types):
            continue

        restype = resource.restype()
        if restype.is_gff():
            file_type = restype.extension.upper()
            if file_types and file_type not in file_types:
                continue

            # Check cache first - if we've already parsed this resource, reuse the parsed GFF
            if resource in gff_cache:
                cached_gff = gff_cache[resource]
                if cached_gff is not None:
                    gff_results = _search_gff_for_resref_with_gff(
                        resource,
                        cached_gff,
                        resref,
                        search_pattern,
                        field_names,
                        field_types,
                        file_type,
                        case_sensitive,
                        logger,
                    )
                    results.extend(gff_results)
            else:
                # Parse the GFF file and cache it
                try:
                    gff = read_gff(resource.data())
                    gff_cache[resource] = gff
                    gff_results = _search_gff_for_resref_with_gff(
                        resource,
                        gff,
                        resref,
                        search_pattern,
                        field_names,
                        field_types,
                        file_type,
                        case_sensitive,
                        logger,
                    )
                    results.extend(gff_results)
                except (ValueError, OSError):
                    gff_cache[resource] = None

        # Search NCS files if requested
        if search_ncs and restype is ResourceType.NCS:
            ncs_results = _search_ncs_for_string(resource, resref, search_pattern, case_sensitive, logger)
            results.extend(ncs_results)

    return results


def find_field_value_references(
    installation: Installation,
    search_value: str,
    *,
    field_names: set[str] | None = None,
    field_types: set[GFFFieldType] | None = None,
    partial_match: bool = False,
    case_sensitive: bool = False,
    file_pattern: str | None = None,
    file_types: set[str] | None = None,
    logger: Callable[[str], None] | None = None,
) -> list[ReferenceSearchResult]:
    """Find all references to a field value in GFF files.

    This is a generic function that can search for any string or resref value in GFF fields.

    Args:
    ----
        installation: The installation to search
        search_value: The value to search for
        field_names: Optional set of specific field names to search
        field_types: Set of GFF field types to search (default: {GFFFieldType.String, GFFFieldType.ResRef})
        partial_match: If True, allow partial matches
        case_sensitive: If True, perform case-sensitive matching
        file_pattern: Optional file pattern to filter results
        file_types: Optional set of file type abbreviations to search
        logger: Optional logging function

    Returns:
    -------
        List of ReferenceSearchResult objects
    """
    if field_types is None:
        field_types = {GFFFieldType.String, GFFFieldType.ResRef}

    # Build search pattern
    search_pattern: re.Pattern[str] = _build_search_pattern(search_value, partial_match, case_sensitive)

    results: list[ReferenceSearchResult] = []

    # Cache parsed GFF files by FileResource to avoid re-parsing the same file
    # This handles cases where the same resource appears multiple times in the installation iterator
    # (e.g., in both override and modules). This is an O(n) -> O(1) optimization for parsing.
    gff_cache: dict[FileResource, GFF | None] = {}

    for resource in installation:
        if not _should_search_resource(resource, file_pattern, file_types, None):
            continue

        restype = resource.restype()
        if restype.is_gff():
            file_type = restype.extension.upper()
            if file_types and file_type not in file_types:
                continue

            # Check cache first - if we've already parsed this resource, reuse the parsed GFF
            if resource in gff_cache:
                cached_gff = gff_cache[resource]
                if cached_gff is not None:
                    gff_results = _search_gff_for_value_with_gff(
                        resource,
                        cached_gff,
                        search_value,
                        search_pattern,
                        field_names,
                        field_types,
                        file_type,
                        case_sensitive,
                        logger,
                    )
                    results.extend(gff_results)
            else:
                # Parse the GFF file and cache it
                try:
                    gff = read_gff(resource.data())
                    gff_cache[resource] = gff
                    gff_results = _search_gff_for_value_with_gff(
                        resource,
                        gff,
                        search_value,
                        search_pattern,
                        field_names,
                        field_types,
                        file_type,
                        case_sensitive,
                        logger,
                    )
                    results.extend(gff_results)
                except (ValueError, OSError):
                    gff_cache[resource] = None

    return results


def _build_search_pattern(value: str, partial_match: bool, case_sensitive: bool) -> re.Pattern[str]:
    """Build a regex pattern for searching."""
    if partial_match:
        pattern = re.escape(value)
    else:
        pattern = rf"\b{re.escape(value)}\b"

    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pattern, flags)


def _should_search_resource(
    resource: FileResource,
    file_pattern: str | None,
    file_types: set[str] | None,
    exclude_types: set[ResourceType] | None,
) -> bool:
    """Check if a resource should be searched based on filters."""
    if exclude_types and resource.restype() in exclude_types:
        return False

    if file_pattern:
        filename = resource.filename()
        if not fnmatch.fnmatch(filename.lower(), file_pattern.lower()):
            return False

    return True


def _search_gff_for_resref(
    resource: FileResource,
    resref: str,
    search_pattern: re.Pattern[str],
    field_names: set[str] | None,
    field_types: set[GFFFieldType],
    file_type: str,
    case_sensitive: bool,
    logger: Callable[[str], None] | None,
) -> list[ReferenceSearchResult]:
    """Search a GFF file for ResRef references."""
    try:
        gff = read_gff(resource.data())
    except (ValueError, OSError):
        return []
    return _search_gff_for_resref_with_gff(resource, gff, resref, search_pattern, field_names, field_types, file_type, case_sensitive, logger)


def _search_gff_for_resref_with_gff(
    resource: FileResource,
    gff: GFF,
    resref: str,
    search_pattern: re.Pattern[str],
    field_names: set[str] | None,
    field_types: set[GFFFieldType],
    file_type: str,
    case_sensitive: bool,
    logger: Callable[[str], None] | None,
) -> list[ReferenceSearchResult]:
    """Search a parsed GFF file for ResRef references."""
    results: list[ReferenceSearchResult] = []

    # Pre-compute search value for direct comparison (faster than regex when possible)
    search_lower = resref.lower() if not case_sensitive else resref
    # Detect if this is a partial match pattern (no word boundaries)
    pattern_str = search_pattern.pattern
    is_partial = "\\b" not in pattern_str
    # Pre-compute ResRef and String type checks (most common case)
    check_resref = GFFFieldType.ResRef in field_types
    check_string = GFFFieldType.String in field_types

    def recurse_struct(gff_struct: GFFStruct, path_prefix: str = "") -> None:
        """Recursively search GFF struct for ResRef matches."""
        # Use direct field access instead of iteration when possible for better performance
        for label, field_type, value in gff_struct:
            # Early exit: skip field name check if we're filtering by field names
            if field_names is not None and label not in field_names:
                # Still need to recurse into nested structures even if we skip this field
                if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                    new_path = f"{path_prefix}.{label}" if path_prefix else label
                    recurse_struct(value, new_path)
                elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                    base_path = f"{path_prefix}.{label}" if path_prefix else label
                    for idx, item in enumerate(value):
                        if isinstance(item, GFFStruct):
                            list_path = f"{base_path}[{idx}]"
                            recurse_struct(item, list_path)
                continue

            # Early exit: skip type check if field type doesn't match
            if field_type not in field_types:
                # Still need to recurse into nested structures
                if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                    new_path = f"{path_prefix}.{label}" if path_prefix else label
                    recurse_struct(value, new_path)
                elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                    base_path = f"{path_prefix}.{label}" if path_prefix else label
                    for idx, item in enumerate(value):
                        if isinstance(item, GFFStruct):
                            list_path = f"{base_path}[{idx}]"
                            recurse_struct(item, list_path)
                continue

            # At this point, we know the field name and type match - check the value
            # Optimize string conversion based on field type
            if field_type == GFFFieldType.ResRef and check_resref:
                # ResRef is already a string subclass, direct access is fastest
                resref_str: str = value  # type: ignore[assignment]
            elif field_type == GFFFieldType.String and check_string:
                resref_str = str(value)
            else:
                # Field type matched but not ResRef or String - shouldn't happen, but skip
                # Still recurse into nested structures
                if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                    new_path = f"{path_prefix}.{label}" if path_prefix else label
                    recurse_struct(value, new_path)
                elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                    base_path = f"{path_prefix}.{label}" if path_prefix else label
                    for idx, item in enumerate(value):
                        if isinstance(item, GFFStruct):
                            list_path = f"{base_path}[{idx}]"
                            recurse_struct(item, list_path)
                continue

            # Fast path: direct comparison for exact matches (avoid regex when possible)
            match_found = False
            if not case_sensitive:
                resref_lower = resref_str.lower()
                if is_partial:
                    match_found = search_lower in resref_lower
                else:
                    match_found = resref_lower == search_lower
            else:
                if is_partial:
                    match_found = resref in resref_str
                else:
                    match_found = resref_str == resref

            # Only use regex if direct comparison didn't match (regex is slower)
            if not match_found:
                match_found = bool(search_pattern.search(resref_str))

            if match_found:
                # Defer string path building until we have a match
                field_path = f"{path_prefix}.{label}" if path_prefix else label
                results.append(
                    ReferenceSearchResult(
                        file_resource=resource,
                        field_path=field_path,
                        matched_value=resref_str,
                        file_type=file_type,
                    ),
                )
                if logger is not None:
                    logger(f"Found '{resref}' in {resource.filename()} at {field_path}")

            # Recurse into nested structures (only once, not multiple times)
            if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                new_path = f"{path_prefix}.{label}" if path_prefix else label
                recurse_struct(value, new_path)
            elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                base_path = f"{path_prefix}.{label}" if path_prefix else label
                for idx, item in enumerate(value):
                    if isinstance(item, GFFStruct):
                        list_path = f"{base_path}[{idx}]"
                        recurse_struct(item, list_path)

    recurse_struct(gff.root)
    return results


def _search_gff_for_value(
    resource: FileResource,
    search_value: str,
    search_pattern: re.Pattern[str],
    field_names: set[str] | None,
    field_types: set[GFFFieldType],
    file_type: str,
    case_sensitive: bool,
    logger: Callable[[str], None] | None,
) -> list[ReferenceSearchResult]:
    """Search a GFF file for string/value references."""
    try:
        gff = read_gff(resource.data())
    except (ValueError, OSError):
        return []
    return _search_gff_for_value_with_gff(
        resource=resource,
        gff=gff,
        search_value=search_value,
        search_pattern=search_pattern,
        field_names=field_names,
        field_types=field_types,
        file_type=file_type,
        case_sensitive=case_sensitive,
        logger=logger,
    )


def _search_gff_for_value_with_gff(
    resource: FileResource,
    gff: GFF,
    search_value: str,
    search_pattern: re.Pattern[str],
    field_names: set[str] | None,
    field_types: set[GFFFieldType],
    file_type: str,
    case_sensitive: bool,
    logger: Callable[[str], None] | None,
) -> list[ReferenceSearchResult]:
    """Search a parsed GFF file for string/value references."""
    results: list[ReferenceSearchResult] = []

    # Pre-compute search value for direct comparison (faster than regex when possible)
    search_lower = search_value.lower() if not case_sensitive else search_value
    # Detect if this is a partial match pattern (no word boundaries)
    pattern_str = search_pattern.pattern
    is_partial = "\\b" not in pattern_str
    # Pre-compute ResRef and String type checks (most common case)
    check_resref = GFFFieldType.ResRef in field_types
    check_string = GFFFieldType.String in field_types

    def recurse_struct(gff_struct: GFFStruct, path_prefix: str = "") -> None:
        """Recursively search GFF struct for value matches."""
        # Use direct field access instead of iteration when possible for better performance
        for label, field_type, value in gff_struct:
            # Early exit: skip field name check if we're filtering by field names
            if field_names is not None and label not in field_names:
                # Still need to recurse into nested structures even if we skip this field
                if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                    new_path = f"{path_prefix}.{label}" if path_prefix else label
                    recurse_struct(value, new_path)
                elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                    base_path = f"{path_prefix}.{label}" if path_prefix else label
                    for idx, item in enumerate(value):
                        if isinstance(item, GFFStruct):
                            list_path = f"{base_path}[{idx}]"
                            recurse_struct(item, list_path)
                continue

            # Early exit: skip type check if field type doesn't match
            if field_type not in field_types:
                # Still need to recurse into nested structures
                if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                    new_path = f"{path_prefix}.{label}" if path_prefix else label
                    recurse_struct(value, new_path)
                elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                    base_path = f"{path_prefix}.{label}" if path_prefix else label
                    for idx, item in enumerate(value):
                        if isinstance(item, GFFStruct):
                            list_path = f"{base_path}[{idx}]"
                            recurse_struct(item, list_path)
                continue

            # At this point, we know the field name and type match - check the value
            # Optimize string conversion based on field type
            if field_type == GFFFieldType.ResRef and check_resref:
                # ResRef is already a string subclass, direct access is fastest
                value_str: str = value  # type: ignore[assignment]
            elif field_type == GFFFieldType.String and check_string:
                value_str = str(value)
            else:
                # Field type matched but not ResRef or String - shouldn't happen, but skip
                # Still recurse into nested structures
                if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                    new_path = f"{path_prefix}.{label}" if path_prefix else label
                    recurse_struct(value, new_path)
                elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                    base_path = f"{path_prefix}.{label}" if path_prefix else label
                    for idx, item in enumerate(value):
                        if isinstance(item, GFFStruct):
                            list_path = f"{base_path}[{idx}]"
                            recurse_struct(item, list_path)
                continue

            # Fast path: direct comparison for exact matches (avoid regex when possible)
            match_found = False
            if not case_sensitive:
                value_lower = value_str.lower()
                if is_partial:
                    match_found = search_lower in value_lower
                else:
                    match_found = value_lower == search_lower
            else:
                if is_partial:
                    match_found = search_value in value_str
                else:
                    match_found = value_str == search_value

            # Only use regex if direct comparison didn't match (regex is slower)
            if not match_found:
                match_found = bool(search_pattern.search(value_str))

            if match_found:
                # Defer string path building until we have a match
                field_path = f"{path_prefix}.{label}" if path_prefix else label
                results.append(
                    ReferenceSearchResult(
                        file_resource=resource,
                        field_path=field_path,
                        matched_value=value_str,
                        file_type=file_type,
                    ),
                )
                if logger is not None:
                    logger(f"Found '{search_value}' in {resource.filename()} at {field_path}")

            # Recurse into nested structures (only once, not multiple times)
            if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                new_path = f"{path_prefix}.{label}" if path_prefix else label
                recurse_struct(value, new_path)
            elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                base_path = f"{path_prefix}.{label}" if path_prefix else label
                for idx, item in enumerate(value):
                    if isinstance(item, GFFStruct):
                        list_path = f"{base_path}[{idx}]"
                        recurse_struct(item, list_path)

    recurse_struct(gff.root)
    return results


def _search_ncs_for_string(
    resource: FileResource,
    search_string: str,
    search_pattern: re.Pattern[str],
    case_sensitive: bool,
    logger: Callable[[str], None] | None,
) -> list[ReferenceSearchResult]:
    """Search an NCS file for string constant references."""
    results: list[ReferenceSearchResult] = []

    try:
        ncs_data = resource.data()
        with BinaryReader.from_auto(ncs_data) as reader:
            # Skip NCS header
            if reader.read_string(4) != "NCS ":
                return results
            if reader.read_string(4) != "V1.0":
                return results
            magic_byte = reader.read_uint8()
            if magic_byte != 0x42:  # noqa: PLR2004
                return results
            total_size = reader.read_uint32(big=True)

            # Search for CONSTS (string constant) instructions
            while reader.position() < total_size and reader.remaining() > 0:
                opcode = reader.read_uint8()
                qualifier = reader.read_uint8()

                # Check if this is CONSTS (opcode=0x04, qualifier=0x05)
                if opcode == NCSByteCode.CONSTx and qualifier == NCSInstructionQualifier.String:
                    string_offset = reader.position()
                    str_len = reader.read_uint16(big=True)
                    if str_len > 0 and reader.remaining() >= str_len:
                        string_value = reader.read_string(str_len, encoding="ascii", errors="ignore")
                        if search_pattern.search(string_value):
                            results.append(
                                ReferenceSearchResult(
                                    file_resource=resource,
                                    field_path="(NCS bytecode)",
                                    matched_value=string_value,
                                    file_type="NCS",
                                    byte_offset=string_offset,
                                ),
                            )
                            if logger is not None:
                                logger(f"Found '{search_string}' in {resource.filename()} at byte offset {string_offset:#X}")

                # Skip to next instruction based on opcode/qualifier
                elif opcode == NCSByteCode.CONSTx:
                    if qualifier == NCSInstructionQualifier.Int:
                        reader.skip(4)
                    elif qualifier == NCSInstructionQualifier.Float:
                        reader.skip(4)
                    elif qualifier == NCSInstructionQualifier.String:
                        str_len = reader.read_uint16(big=True)
                        reader.skip(str_len)
                    elif qualifier == NCSInstructionQualifier.Object:
                        reader.skip(4)
                elif opcode in (NCSByteCode.CPDOWNSP, NCSByteCode.CPTOPSP, NCSByteCode.CPDOWNBP, NCSByteCode.CPTOPBP):
                    reader.skip(6)
                elif opcode == NCSByteCode.STORE_STATE:
                    reader.skip(8)
                elif opcode in (
                    NCSByteCode.CPDOWNBP,
                    NCSByteCode.CPTOPBP,
                    NCSByteCode.DECxBP,
                    NCSByteCode.DECxSP,
                    NCSByteCode.INCxBP,
                    NCSByteCode.INCxSP,
                    NCSByteCode.JMP,
                    NCSByteCode.JNZ,
                    NCSByteCode.JSR,
                    NCSByteCode.JZ,
                    NCSByteCode.MOVSP,
                ):
                    reader.skip(4)
                elif opcode == NCSByteCode.ACTION:
                    reader.skip(3)
                elif opcode == NCSByteCode.DESTRUCT:
                    reader.skip(6)
                elif opcode == NCSByteCode.EQUALxx and qualifier == NCSInstructionQualifier.StructStruct:
                    reader.skip(2)
                elif opcode == NCSByteCode.NEQUALxx and qualifier == NCSInstructionQualifier.StructStruct:
                    reader.skip(2)
                # Other instructions have no additional data

    except Exception:  # noqa: BLE001
        # If anything fails, return what we found so far
        pass

    return results
