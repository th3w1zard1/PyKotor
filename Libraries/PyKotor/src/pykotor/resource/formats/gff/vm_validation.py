"""GFF validation for engine compatibility.

This module provides validation functions for GFF files to ensure they
are compatible with the game's engine based on reverse engineering analysis
of the CResGFF class in swkotor.exe.

Key findings from reverse engineering:
- CResGFF uses specific capacity tracking for dynamic arrays
- Header, structs, fields, and labels are stored in separate arrays
- Field data is stored separately with indices
- 16-byte labels are used throughout
- Capacity fields prevent buffer overflows
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF

logger = RobustLogger("pykotor.resource.formats.gff.vm_validation")


def validate_gff_for_engine(gff: GFF) -> None:
    """Validate a GFF file for compatibility with the game engine.

    Based on reverse engineering of CResGFF class, this function checks
    for structural issues that could cause engine problems.

    Args:
    ----
        gff: The GFF object to validate

    Raises:
    ------
        ValueError: If validation fails with details about the issue
    """
    issues = []

    # Validate struct hierarchy
    _validate_struct_hierarchy(gff, issues)

    # Check field data integrity
    _validate_field_data_integrity(gff, issues)

    # Validate label usage (16-byte limit)
    _validate_label_constraints(gff, issues)

    # Check for potential performance issues
    _validate_performance_constraints(gff, issues)

    if issues:
        error_msg = f"GFF validation failed with {len(issues)} issue(s):\n" + "\n".join(f"  - {issue}" for issue in issues)
        raise ValueError(error_msg)


def _validate_struct_hierarchy(gff: GFF, issues: list[str]) -> None:
    """Validate the struct hierarchy for engine compatibility."""
    # Check for excessively deep nesting (based on engine limitations)
    max_depth = _calculate_max_struct_depth(gff.root)
    if max_depth > 10:  # Conservative limit based on typical GFF complexity
        issues.append(f"Struct hierarchy is unusually deep (max depth: {max_depth})")

    # Validate struct IDs are reasonable
    struct_ids = set()
    def collect_struct_ids(struct):
        if struct.struct_id in struct_ids:
            issues.append(f"Duplicate struct ID: {struct.struct_id}")
        else:
            struct_ids.add(struct.struct_id)
        for child in struct:
            if hasattr(child, 'value') and hasattr(child.value, '__iter__'):
                for item in child.value:
                    if hasattr(item, 'struct_id'):
                        collect_struct_ids(item)

    collect_struct_ids(gff.root)


def _validate_field_data_integrity(gff: GFF, issues: list[str]) -> None:
    """Validate field data integrity."""
    # Check for empty or invalid field names
    for struct in _iterate_all_structs(gff.root):
        for field in struct:
            if not field.label or len(field.label.strip()) == 0:
                issues.append(f"Struct {struct.struct_id} has field with empty label")

            # Check label length (based on 16-byte engine limit)
            if len(field.label.encode('utf-8')) > 16:
                issues.append(f"Field label '{field.label}' exceeds 16-byte engine limit")


def _validate_label_constraints(gff: GFF, issues: list[str]) -> None:
    """Validate label constraints based on engine requirements."""
    labels_seen = set()

    for struct in _iterate_all_structs(gff.root):
        for field in struct:
            label_bytes = field.label.encode('utf-8')

            # Engine uses 16-byte labels
            if len(label_bytes) > 16:
                issues.append(f"Label '{field.label}' is {len(label_bytes)} bytes (engine limit: 16)")

            # Check for null bytes in labels (engine may not handle this well)
            if b'\x00' in label_bytes:
                issues.append(f"Label '{field.label}' contains null bytes")

            # Track duplicate labels (may cause lookup issues)
            if field.label in labels_seen:
                issues.append(f"Duplicate field label: '{field.label}'")
            else:
                labels_seen.add(field.label)


def _validate_performance_constraints(gff: GFF, issues: list[str]) -> None:
    """Validate for potential performance issues."""
    total_structs = sum(1 for _ in _iterate_all_structs(gff.root))
    total_fields = sum(len(struct) for struct in _iterate_all_structs(gff.root))

    # Check for files that might be too large for efficient loading
    if total_structs > 10000:  # Conservative limit
        issues.append(f"GFF has unusually many structs ({total_structs})")

    if total_fields > 50000:  # Conservative limit
        issues.append(f"GFF has unusually many fields ({total_fields})")

    # Check for structs with too many fields
    for struct in _iterate_all_structs(gff.root):
        if len(struct) > 1000:  # Conservative limit
            issues.append(f"Struct {struct.struct_id} has too many fields ({len(struct)})")


def _calculate_max_struct_depth(struct) -> int:
    """Calculate the maximum depth of the struct hierarchy."""
    if not hasattr(struct, '__iter__'):
        return 0

    max_child_depth = 0
    for field in struct:
        if hasattr(field, 'value') and hasattr(field.value, '__iter__'):
            for item in field.value:
                if hasattr(item, 'struct_id'):  # It's a struct
                    child_depth = _calculate_max_struct_depth(item)
                    max_child_depth = max(max_child_depth, child_depth)

    return max_child_depth + 1


def _iterate_all_structs(root_struct):
    """Iterate through all structs in the GFF hierarchy."""
    yield root_struct

    for field in root_struct:
        if hasattr(field, 'value') and hasattr(field.value, '__iter__'):
            for item in field.value:
                if hasattr(item, 'struct_id'):  # It's a struct
                    yield from _iterate_all_structs(item)
