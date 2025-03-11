"""Factory for creating ASCII MDL node readers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.io.ascii.nodes.aabb_reader import MDLASCIIAABBReader
from pykotor.resource.formats.mdl.io.ascii.nodes.anim_reader import MDLASCIIAnimationReader
from pykotor.resource.formats.mdl.io.ascii.nodes.dangly_reader import MDLASCIIDanglyReader
from pykotor.resource.formats.mdl.io.ascii.nodes.dummy_reader import MDLASCIIDummyReader
from pykotor.resource.formats.mdl.io.ascii.nodes.emitter_reader import MDLASCIIEmitterReader
from pykotor.resource.formats.mdl.io.ascii.nodes.light_reader import MDLASCIILightReader
from pykotor.resource.formats.mdl.io.ascii.nodes.reference_reader import MDLASCIIReferenceReader
from pykotor.resource.formats.mdl.io.ascii.nodes.saber_reader import MDLASCIISaberReader
from pykotor.resource.formats.mdl.io.ascii.nodes.skin_reader import MDLASCIISkinReader
from pykotor.resource.formats.mdl.io.ascii.nodes.trimesh_reader import MDLASCIITrimeshReader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
    from pykotor.resource.formats.mdl.io.ascii.nodes.base_node_reader import MDLASCIINodeReader


# Map of node type strings to reader classes
NODE_TYPE_MAP = {
    "animation": MDLASCIIAnimationReader,
    "saber": MDLASCIISaberReader,
    "trimesh": MDLASCIITrimeshReader,
    "dummy": MDLASCIIDummyReader,
    "light": MDLASCIILightReader,
    "emitter": MDLASCIIEmitterReader,
    "reference": MDLASCIIReferenceReader,
    "skin": MDLASCIISkinReader,
    "dangly": MDLASCIIDanglyReader,
    "aabb": MDLASCIIAABBReader,
    "lightsaber": MDLASCIISaberReader,  # Alternative name for saber nodes
}


class MDLASCIINodeReaderFactory:
    """Factory for creating ASCII MDL node readers."""

    def __init__(self, reader: BinaryReader, names: list[str], node_by_number: dict[int, MDLNode]):
        """Initialize the factory.

        Args:
            reader: Reader for MDL data
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        self._reader = reader
        self._names = names
        self._node_by_number = node_by_number

    def create_reader(self, node_type: str, node_name: str) -> MDLASCIINodeReader:
        """Create a reader for the given node type.

        Args:
            node_type: Type of node to create reader for
            node_name: Name of the node

        Returns:
            MDLASCIINodeReader: The created reader

        Raises:
            MDLReadError: If node type is unknown or invalid
        """
        # Validate input
        if not node_type:
            raise MDLReadError("Node type cannot be empty")

        # Convert to lowercase for case-insensitive comparison
        node_type = node_type.casefold()

        # Handle saber nodes marked with 2081__ prefix
        if node_name.startswith("2081__") and node_type == "trimesh":
            return MDLASCIISaberReader(self._reader, self._names, self._node_by_number)

        # Get reader class for node type
        reader_class = NODE_TYPE_MAP.get(node_type)
        assert reader_class is not None, f"Unknown node type: '{node_type}' for node '{node_name}'"

        # Create and return reader instance
        return reader_class(self._reader, self._names, self._node_by_number)


def create_ascii_node_reader(
    node_type: str,
    reader: BinaryReader,
    names: list[str],
    node_by_number: dict[int, MDLNode],
) -> MDLASCIINodeReader:
    """Create a reader for the given node type.

    Args:
        node_type: Type of node to create reader for
        reader: Reader for MDL data
        names: List of names from the MDL file
        node_by_number: Dictionary mapping node numbers to nodes

    Returns:
        MDLASCIINodeReader: The created reader

    Raises:
        MDLReadError: If node type is unknown or invalid
    """
    factory = MDLASCIINodeReaderFactory(reader, names, node_by_number)
    return factory.create_reader(node_type, names[-1] if names else "")