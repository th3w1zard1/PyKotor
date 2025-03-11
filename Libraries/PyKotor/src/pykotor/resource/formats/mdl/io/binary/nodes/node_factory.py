"""Factory for creating appropriate node readers based on node flags."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from pykotor.resource.formats.mdl.io.binary.nodes.aabb_reader import MDLBinaryAABBReader
from pykotor.resource.formats.mdl.io.binary.nodes.anim_reader import MDLBinaryAnimationReader
from pykotor.resource.formats.mdl.io.binary.nodes.dangly_reader import MDLBinaryDanglyReader
from pykotor.resource.formats.mdl.io.binary.nodes.default_reader import MDLDefaultBinaryNodeReader
from pykotor.resource.formats.mdl.io.binary.nodes.emitter_reader import MDLBinaryEmitterReader
from pykotor.resource.formats.mdl.io.binary.nodes.light_reader import MDLBinaryLightReader
from pykotor.resource.formats.mdl.io.binary.nodes.reference_reader import MDLBinaryReferenceReader
from pykotor.resource.formats.mdl.io.binary.nodes.saber_reader import MDLBinarySaberReader
from pykotor.resource.formats.mdl.io.binary.nodes.skin_reader import MDLBinarySkinReader
from pykotor.resource.formats.mdl.io.binary.nodes.trimesh_reader import MDLBinaryTrimeshReader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
    from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader


class MDLBinaryNodeReaderFactory:
    """Factory for creating node readers based on node flags."""

    # Node type flags
    FLAG_DUMMY = 0x0001  # Empty node
    FLAG_REFERENCE = 0x0010  # Reference to another model
    FLAG_MESH = 0x0020  # Base mesh type
    FLAG_SKIN = 0x0040  # Skinned mesh
    FLAG_DANGLY = 0x0080  # Cloth/soft body mesh
    FLAG_AABB = 0x0100  # Axis-aligned bounding box
    FLAG_ANIM = 0x0200  # Animation
    FLAG_LIGHT = 0x0002  # Dynamic light
    FLAG_EMITTER = 0x0004  # Particle emitter
    FLAG_CAMERA = 0x0008  # Camera
    FLAG_SABER = 0x0400  # Lightsaber node

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader, names: List[str], node_by_number: Dict[int, MDLNode]):
        """Initialize the factory.

        Args:
            mdl_reader: The reader to use for reading node data
            mdx_reader: The reader to use for reading MDX data
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        self._mdl_reader: BinaryReader = mdl_reader
        self._mdx_reader: BinaryReader = mdx_reader
        self._names: list[str] = names
        self._node_by_number: dict[int, MDLNode] = node_by_number

    def create_reader(self, node_flags: int) -> MDLBinaryNodeReader:
        """Create appropriate reader based on node flags.

        Args:
            node_flags: The node flags indicating the type

        Returns:
            MDLBinaryNodeReader: The appropriate reader for the node type

        Raises:
            MDLReadError: If no reader exists for the node type
        """
        # Check flags in order of specificity
        if node_flags & self.FLAG_ANIM:  # Animation
            return MDLBinaryAnimationReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        elif node_flags & self.FLAG_AABB:  # AABB
            return MDLBinaryAABBReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        elif node_flags & self.FLAG_DANGLY:  # Dangly
            return MDLBinaryDanglyReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        elif node_flags & self.FLAG_SKIN:  # Skin
            return MDLBinarySkinReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        elif node_flags & self.FLAG_SABER:  # Saber
            return MDLBinarySaberReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        elif node_flags & self.FLAG_MESH:  # Mesh
            return MDLBinaryTrimeshReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        elif node_flags & self.FLAG_LIGHT:  # Light
            return MDLBinaryLightReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        elif node_flags & self.FLAG_EMITTER:  # Emitter
            return MDLBinaryEmitterReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        elif node_flags & self.FLAG_REFERENCE:  # Reference
            return MDLBinaryReferenceReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
        else:
            # Return default reader for unimplemented types
            return MDLDefaultBinaryNodeReader(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
