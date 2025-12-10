from __future__ import annotations

from enum import Enum
from typing import Any

import qtpy


def sip_enum_to_int(obj: Any) -> int:
    # First check if it's already an int
    if isinstance(obj, int):
        return obj
    # Check if it's a Python Enum (has value attribute)
    if isinstance(obj, Enum):
        return sip_enum_to_int(obj.value)
    # Check if it has a value attribute (Qt6 enum or other enum-like objects)
    # Try to access value attribute directly - if it exists, use it
    try:
        value_attr = obj.value  # type: ignore[attr-defined]
        return sip_enum_to_int(value_attr)
    except AttributeError:
        # Object doesn't have value attribute, continue to other checks
        pass
    # For Qt5 SIP enums, try to convert directly
    if qtpy.QT5:
        return int(obj)
    # Last resort: try to convert to int
    return int(obj)
