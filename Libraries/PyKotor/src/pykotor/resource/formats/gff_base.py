from __future__ import annotations

from typing import Any, Dict


class GFFBase:
    """Base class for GFF objects that handles unknown fields."""

    def __init__(self):
        # Initialize internal dict for unknown fields
        self._raw_fields: Dict[str, Any] = {}

    def set_raw_field(self, name: str, value: Any) -> None:
        """Set an unknown field."""
        self._raw_fields[name] = value

    def get_raw_field(self, name: str, default: Any = None) -> Any:
        """Get an unknown field."""
        return self._raw_fields.get(name, default)

    def get_all_raw_fields(self) -> Dict[str, Any]:
        """Retrieve all unknown fields."""
        return self._raw_fields.copy()