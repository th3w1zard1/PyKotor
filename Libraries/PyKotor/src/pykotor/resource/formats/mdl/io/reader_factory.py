"""Factory for creating appropriate MDL readers based on file content."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.io.ascii import ASCIIMDLReader
from pykotor.resource.formats.mdl.io.binary import BinaryMDLReader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.io.base_reader import MDLReader


class MDLReaderFactory:
    """Factory for creating MDL readers."""

    @staticmethod
    def create_reader(mdl_reader: BinaryReader) -> MDLReader:
        """Create appropriate reader based on file content.

        Args:
            mdl_reader: The reader containing MDL file data

        Returns:
            MDLReader: The appropriate reader for the file format

        Raises:
            ValueError: If file format cannot be determined
        """
        # Save current position
        old_pos = mdl_reader.tell()

        try:
            # Check for ASCII format
            # ASCII MDL files start with "# MDL ASCII"
            header = mdl_reader.read(11).decode("ascii", errors="ignore")
            if header == "# MDL ASCII":
                return ASCIIMDLReader(mdl_reader)

            # If not ASCII, assume binary
            # Binary MDL files start with function pointers
            return BinaryMDLReader(mdl_reader)

        finally:
            # Restore position
            mdl_reader.seek(old_pos)