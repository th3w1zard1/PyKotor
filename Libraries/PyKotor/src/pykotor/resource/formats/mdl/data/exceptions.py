"""Exceptions for MDL format handling."""
from __future__ import annotations


class MDLError(Exception):
    """Base exception for MDL format errors."""
    pass


class MDLFormatError(MDLError):
    """Exception raised when the MDL file format is invalid."""
    pass


class MDLVersionError(MDLFormatError):
    """Exception raised when the MDL file version is unsupported."""
    pass


class MDLValidationError(MDLError):
    """Exception raised when MDL data validation fails."""
    pass


class MDLReadError(MDLError):
    """Exception raised when reading MDL data fails."""
    pass


class MDLWriteError(MDLError):
    """Exception raised when writing MDL data fails."""
    pass


class MDLNodeError(MDLError):
    """Exception raised for node-related errors."""
    pass


class MDLControllerError(MDLError):
    """Exception raised for animation controller errors."""
    pass


class MDLGeometryError(MDLError):
    """Exception raised for geometry-related errors."""
    pass


class MDLAnimationError(MDLError):
    """Exception raised for animation-related errors."""
    pass
