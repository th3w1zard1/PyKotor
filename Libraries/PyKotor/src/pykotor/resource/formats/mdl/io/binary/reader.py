"""Binary MDL file reader implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.data.enums import MDLClassification, MDLNodeFlags
from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
from pykotor.resource.formats.mdl.io.base_reader import MDLReader

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.data.model import MDL


@dataclass
class ArrayDefinition:
    """Array definition in MDL format."""

    offset: int
    count: int
    count2: int


class BinaryMDLReader(MDLReader):
    """Reader for binary MDL files."""

    def read(self) -> MDL:
        """Read the binary MDL file and return the model.

        Returns:
            MDL: The loaded model
        """
        # Read file header
        self._mdl_reader.skip(4)  # unknown
        mdl_size = self._mdl_reader.read_uint32()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.
        mdx_size = self._mdl_reader.read_uint32()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.

        # Read geometry header
        func_ptr1 = self._mdl_reader.read_uint32()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.
        func_ptr2 = self._mdl_reader.read_uint32()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.
        self._mdl.name = self._mdl_reader.read_terminated_string("\0", 32)
        self._mdl.type = self._mdl_reader.read_terminated_string("\0", 32)

        # Skip runtime arrays
        self._mdl_reader.skip(24)  # 2 arrays of 3 uint32s

        # Read geometry header
        self._mdl.bounding_min = self._mdl_reader.read_vector3()
        self._mdl.bounding_max = self._mdl_reader.read_vector3()
        self._mdl.radius = self._mdl_reader.read_single()
        self._mdl.animation_scale = self._mdl_reader.read_single()

        # Read array definitions
        names_count = self._mdl_reader.read_uint32()
        names_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        nodes_count = self._mdl_reader.read_uint32()
        nodes_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        animations_count = self._mdl_reader.read_uint32()
        animations_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        # Read model header
        classification = self._mdl_reader.read_uint8()
        subclassification = self._mdl_reader.read_uint8()
        _ = self._mdl_reader.read_uint8()  # unknown
        affected_by_fog = self._mdl_reader.read_uint8()
        num_child_models = self._mdl_reader.read_uint32()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.

        # Read animation array definition
        anim_array_def = self._read_array_definition()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.

        # Read supermodel reference
        supermodel_ref = self._mdl_reader.read_uint32()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.
        supermodel_name = self._mdl_reader.read_terminated_string("\0", 32)
        if supermodel_name == "NULL":
            supermodel_name = ""

        # Read MDX info
        mdx_size2 = self._mdl_reader.read_uint32()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.
        mdx_offset = self._mdl_reader.read_uint32()  # FIXME: unused?? store/use it somehow, check kotorblender/mdlops in the vendor folder.

        # Set model properties
        self._mdl.classification = MDLClassification(classification)
        self._mdl.subclassification = subclassification
        self._mdl.affected_by_fog = bool(affected_by_fog)
        self._mdl.supermodel = supermodel_name

        # Load data
        if names_count > 0:
            self._load_names(names_offset, names_count)

        if nodes_count > 0:
            self._peek_nodes(nodes_offset, nodes_count)
            self._load_nodes(nodes_offset, nodes_count)

        if animations_count > 0:
            self._load_animations(animations_offset, animations_count)

        return self._mdl

    def _read_array_definition(self) -> ArrayDefinition:
        """Read an array definition.

        Returns:
            ArrayDefinition: The array definition
        """
        offset = self._mdl_reader.read_uint32()
        count = self._mdl_reader.read_uint32()
        count2 = self._mdl_reader.read_uint32()

        if count != count2:
            raise ValueError(f"Array count mismatch: count={count}, count2={count2}")

        return ArrayDefinition(offset, count, count2)

    def _load_names(self, offset: int, count: int) -> None:
        """Load the names list from the file.

        Args:
            offset: Offset to names data
            count: Number of names to load
        """
        self._mdl_reader.seek(12 + offset)
        name_offsets = [self._mdl_reader.read_uint32() for _ in range(count)]

        for offset in name_offsets:
            self._mdl_reader.seek(12 + offset)
            self._names.append(self._mdl_reader.read_terminated_string("\0"))

    def _peek_nodes(self, offset: int, count: int) -> None:
        """Pre-scan nodes to build node lookup table.

        Args:
            offset: Offset to nodes data
            count: Number of nodes to scan
        """
        old_pos = self._mdl_reader.tell()
        self._mdl_reader.seek(12 + offset)
        node_offsets = [self._mdl_reader.read_uint32() for _ in range(count)]

        for node_offset in node_offsets:
            self._mdl_reader.seek(12 + node_offset)

            # Skip function pointers
            self._mdl_reader.skip(8)

            # Read node header
            type_flags = self._mdl_reader.read_uint16()
            node_number = self._mdl_reader.read_uint16()
            name_index = self._mdl_reader.read_uint16()

            # Create placeholder node
            node = MDLNode(self._names[name_index])
            node.node_number = node_number
            node.node_flags = MDLNodeFlags(type_flags)

            self._node_by_number[node_number] = node

        self._mdl_reader.seek(old_pos)

    def _load_nodes(self, offset: int, count: int) -> None:
        """Load all nodes from the file.

        Args:
            offset: Offset to nodes data
            count: Number of nodes to load
        """
        from pykotor.resource.formats.mdl.io.binary.nodes.node_factory import MDLNodeReaderFactory

        self._mdl_reader.seek(12 + offset)
        node_offsets = [self._mdl_reader.read_uint32() for _ in range(count)]

        factory = MDLNodeReaderFactory(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)

        for node_offset in node_offsets:
            self._mdl_reader.seek(12 + node_offset)

            # Skip function pointers
            self._mdl_reader.skip(8)

            # Read node type
            type_flags = self._mdl_reader.read_uint16()
            self._mdl_reader.seek(12 + node_offset)  # Reset position

            # Create appropriate reader and read node
            reader = factory.create_reader(type_flags)
            node = reader.read_node(node_offset)

            # Add node to model
            self._mdl.nodes.append(node)

    def _load_animations(self, offset: int, count: int) -> None:
        """Load all animations from the file.

        Args:
            offset: Offset to animations data
            count: Number of animations to load
        """
        from pykotor.resource.formats.mdl.io.binary.nodes.node_factory import MDLNodeReaderFactory

        self._mdl_reader.seek(12 + offset)
        anim_offsets = [self._mdl_reader.read_uint32() for _ in range(count)]

        factory = MDLNodeReaderFactory(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)

        for anim_offset in anim_offsets:
            self._mdl_reader.seek(12 + anim_offset)

            # Skip function pointers
            self._mdl_reader.skip(8)

            # Read animation header
            type_flags = self._mdl_reader.read_uint16()
            self._mdl_reader.seek(12 + anim_offset)  # Reset position

            # Create animation reader and read animation
            reader = factory.create_reader(type_flags)
            anim = reader.read_node(anim_offset)

            # Add animation to model
            self._mdl.anims.append(anim)
