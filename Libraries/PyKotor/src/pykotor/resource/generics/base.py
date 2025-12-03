"""Base class for generic resource types to preserve original field values.

This module provides a base class that generic resource types (ARE, DLG, JRL, etc.)
can inherit from to preserve original field values when loading and saving resources.
This ensures that fields not represented in the UI are preserved during roundtrip operations.
"""
from __future__ import annotations

from typing import Any


class GenericBase:
    """Base class for generic resource types that need to preserve original field values.
    
    This class provides functionality to store and retrieve original field values,
    which is essential for roundtrip operations where some fields may not be
    represented in the UI but should still be preserved.
    
    Usage:
    ------
        class ARE(GenericBase):
            def __init__(self):
                super().__init__()
                self.version: int = 0
                # ... other fields ...
            
            def preserve_original(self):
                super().preserve_original()
                # Store original values after loading
                self._store_original('version', self.version)
                # ... store other fields ...
    """
    
    def __init__(self):
        """Initialize the base class with empty original values storage."""
        self._original_values: dict[str, Any] = {}
        self._has_original: bool = False
    
    def preserve_original(self) -> None:
        """Mark that original values should be preserved.
        
        Call this method after loading a resource to indicate that the current
        state represents the original values that should be preserved.
        """
        self._has_original = True
    
    def _store_original(self, field_name: str, value: Any) -> None:
        """Store an original field value.
        
        Args:
        ----
            field_name: Name of the field to store
            value: Original value of the field
        """
        if self._has_original:
            self._original_values[field_name] = value
    
    def get_original_or_current(
        self,
        field_name: str,
        current_value: Any,
        default_value: Any,
    ) -> Any:
        """Get original value if current is at default, otherwise return current.
        
        This method is used during dismantle operations to preserve original
        values for fields that haven't been modified (are at their default).
        
        Args:
        ----
            field_name: Name of the field
            current_value: Current value of the field
            default_value: Default value for the field
            
        Returns:
        -------
            Original value if current equals default and original exists,
            otherwise returns current value
        """
        if not self._has_original:
            return current_value
        
        # If current value is at default and we have an original, use original
        if current_value == default_value and field_name in self._original_values:
            return self._original_values[field_name]
        
        return current_value
    
    def clear_original(self) -> None:
        """Clear stored original values.
        
        Call this when creating a new resource (not loading from file)
        to ensure original values aren't incorrectly preserved.
        """
        self._original_values.clear()
        self._has_original = False

