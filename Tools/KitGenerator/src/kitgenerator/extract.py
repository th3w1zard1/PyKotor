"""Kit extraction from RIM and ERF files.

This module provides a thin wrapper around pykotor.tools.kit.extract_kit
for the KitGenerator tool.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from loggerplus import RobustLogger

    from pykotor.extract.installation import Installation

# Import the business logic from the library
from pykotor.tools.kit import extract_kit as _extract_kit


def extract_kit(
    installation: Installation,
    module_name: str,
    output_path: Path,
    *,
    kit_id: str | None = None,
    logger: RobustLogger | None = None,
) -> None:
    """Extract kit resources from module RIM or ERF files.

    This is a thin wrapper around pykotor.tools.kit.extract_kit that provides
    the same interface for the KitGenerator tool.

    Args:
    ----
        installation: The game installation instance
        module_name: The module name (e.g., "danm13" or "danm13.mod")
        output_path: Path where the kit should be generated
        kit_id: Optional kit identifier (defaults to module_name.lower())
        logger: Optional logger instance for progress reporting

    Raises:
    ------
        FileNotFoundError: If no valid RIM or ERF files are found for the module
        ValueError: If the module name format is invalid
    """
    # Delegate to the library function
    _extract_kit(
        installation=installation,
        module_name=module_name,
        output_path=output_path,
        kit_id=kit_id,
        logger=logger,
    )
