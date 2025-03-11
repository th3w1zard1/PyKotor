from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pykotor.common.misc import ResRef
from pykotor.resource.formats.mdl.data.enums import MDLModelFlags, MDLModelType
from pykotor.resource.formats.mdl.io.binary.headers import _GeometryHeader
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter


class _ModelHeader:
    """Header data for the overall model file.

    The model header contains all the metadata and data offsets needed to describe
    a complete model.

    Contains metadata including its classification, animations,
    bounding geometry, and references to other models.

    Attributes:
        geometry (_GeometryHeader): Geometry header associated with the model.
        model_type (MDLModelType): Classification of the model (effect, tile, character, etc).
        model_flags (MDLModelFlags): Flags affecting the behavior of the model.
        padding0 (int): Padding for alignment.
        affected_by_fog (bool): Indicates whether fog affects this model.
        child_model_count (int): Number of child models referenced.
        offset_to_animations (int): Offset to the animations data.
        animation_count (int): Number of animations associated with the model.
        animation_count2 (int): Duplicate of animation_count for validation.
        parent_model_index (int): Index into the parent model array if this is a child model.
        bounding_box_min (Vector3): Minimum point of the model's bounding box.
        bounding_box_max (Vector3): Maximum point of the model's bounding box.
        radius (float): Radius of the bounding sphere.
        anim_scale (float): Scale factor for animations.
        supermodel (ResRef): Name of the parent model to inherit from.
        offset_to_super_root (int): Offset to the root node of the parent model.
        model_flags2 (int): Additional flags affecting model behavior.
        mdx_size (int): Size of the MDX data.
        mdx_offset (int): Offset to the MDX data.
        offset_to_name_offsets (int): Offset to the name offsets.
        name_offsets_count (int): Count of name offsets.
        name_offsets_count2 (int): Duplicate of name_offsets_count for validation.
    """

    SIZE: ClassVar[Literal[92]] = 92
    """Size of model header in bytes."""

    def __init__(self):
        self.geometry: _GeometryHeader = _GeometryHeader()
        self.model_type: MDLModelType = MDLModelType.INVALID
        self.model_flags: MDLModelFlags = MDLModelFlags.NONE
        self.padding0: int = 0
        self.affected_by_fog: bool = False
        self.child_model_count: int = 0
        self.offset_to_animations: int = 0
        self.animation_count: int = 0
        self.animation_count2: int = 0
        self.parent_model_index: int = 0
        self.bounding_box_min: Vector3 = Vector3.from_null()
        self.bounding_box_max: Vector3 = Vector3.from_null()
        self.radius: float = 0.0
        self.anim_scale: float = 1.0
        self.supermodel: ResRef = ResRef.from_blank()
        self.offset_to_super_root: int = 0
        self.model_flags2: int = 0
        self.mdx_size: int = 0
        self.mdx_offset: int = 0
        self.offset_to_name_offsets: int = 0
        self.name_offsets_count: int = 0
        self.name_offsets_count2: int = 0

    def read(self, reader: BinaryReader) -> _ModelHeader:
        """Read model header data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated model header instance.
        """
        self.geometry = _GeometryHeader().read(reader)
        self.model_type = MDLModelType(reader.read_uint8())
        self.model_flags = MDLModelFlags(reader.read_uint8())
        self.padding0 = reader.read_uint8()
        self.affected_by_fog = bool(reader.read_uint8())
        self.child_model_count = reader.read_uint32()
        self.offset_to_animations = reader.read_uint32()
        self.animation_count = reader.read_uint32()
        self.animation_count2 = reader.read_uint32()
        self.parent_model_index = reader.read_uint32()
        self.bounding_box_min = reader.read_vector3()
        self.bounding_box_max = reader.read_vector3()
        self.radius = reader.read_single()
        self.anim_scale = reader.read_single()
        self.supermodel = ResRef(reader.read_terminated_string("\0", 32))
        self.offset_to_super_root = reader.read_uint32()
        self.model_flags2 = reader.read_uint32()
        self.mdx_size = reader.read_uint32()
        self.mdx_offset = reader.read_uint32()
        self.offset_to_name_offsets = reader.read_uint32()
        self.name_offsets_count = reader.read_uint32()
        self.name_offsets_count2 = reader.read_uint32()
        return self

    def write(self, writer: BinaryWriter):
        """Write model header data to a binary stream.

        Args:
            writer: Binary writer to write data to.
        """
        self.geometry.write(writer)
        writer.write_uint8(self.model_type.value)
        writer.write_uint8(self.model_flags.value)
        writer.write_uint8(self.padding0)
        writer.write_uint8(int(self.affected_by_fog))
        writer.write_uint32(self.child_model_count)
        writer.write_uint32(self.offset_to_animations)
        writer.write_uint32(self.animation_count)
        writer.write_uint32(self.animation_count2)
        writer.write_uint32(self.parent_model_index)
        writer.write_vector3(self.bounding_box_min)
        writer.write_vector3(self.bounding_box_max)
        writer.write_single(self.radius)
        writer.write_single(self.anim_scale)
        writer.write_string(str(self.supermodel), string_length=32, encoding="ascii", errors="ignore")
        writer.write_uint32(self.offset_to_super_root)
        writer.write_uint32(self.model_flags2)
        writer.write_uint32(self.mdx_size)
        writer.write_uint32(self.mdx_offset)
        writer.write_uint32(self.offset_to_name_offsets)
        writer.write_uint32(self.name_offsets_count)
        writer.write_uint32(self.name_offsets_count2)
