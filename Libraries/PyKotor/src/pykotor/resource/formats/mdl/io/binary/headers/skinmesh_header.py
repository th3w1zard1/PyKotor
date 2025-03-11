from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pykotor.common.misc import Game
from pykotor.resource.formats.mdl.io.binary.headers.trimesh_header import _TrimeshHeader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter
    from utility.common.geometry import Vector3, Vector4


class _SkinmeshHeader(_TrimeshHeader):
    """Header data for skinned mesh nodes.

    Extends the trimesh header with additional data for skinned meshes,
    including bone weights and transforms.

    A skinned mesh contains vertex weights and bone mappings that allow the mesh
    to be deformed by skeletal animations.

    Attributes:
        unknown2 (int): Unknown value.
        unknown3 (int): Unknown value.
        unknown4 (int): Unknown value.
        offset_to_mdx_weights (int): Offset to vertex weight data in MDX.
        offset_to_mdx_bones (int): Offset to vertex bone indices in MDX.
        offset_to_bonemap (int): Offset to bone mapping data.
        bonemap_count (int): Number of bone map entries.
        offset_to_qbones (int): Offset to quaternion bone transforms.
        qbones_count (int): Number of quaternion transforms.
        qbones_count2 (int): Duplicate of qbones_count.
        offset_to_tbones (int): Offset to translation bone transforms.
        tbones_count (int): Number of translation transforms.
        tbones_count2 (int): Duplicate of tbones_count.
        offset_to_unknown0 (int): Unknown offset.
        unknown0_count (int): Unknown count.
        unknown0_count2 (int): Duplicate of unknown0_count.
        bones (tuple[int, ...]): Array of bone indices.
        unknown1 (int): Unknown value.
        bonemap (list[int]): Bone mapping data.
        tbones (list[Vector3]): Translation bone transforms.
        qbones (list[Vector4]): Quaternion bone transforms.
    """

    K1_SIZE: ClassVar[Literal[432]] = 432
    """Size of the header in bytes for KotOR 1."""

    K2_SIZE: ClassVar[Literal[440]] = 440
    """Size of the header in bytes for KotOR 2."""

    def __init__(self):
        super().__init__()
        self.unknown2: int = 0  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.unknown3: int = 0  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.unknown4: int = 0  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.offset_to_mdx_weights: int = 0
        self.offset_to_mdx_bones: int = 0
        self.offset_to_bonemap: int = 0
        self.bonemap_count: int = 0
        self.offset_to_qbones: int = 0
        self.qbones_count: int = 0
        self.qbones_count2: int = 0
        self.offset_to_tbones: int = 0
        self.tbones_count: int = 0
        self.tbones_count2: int = 0
        self.offset_to_unknown0: int = 0
        self.unknown0_count: int = 0  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.unknown0_count2: int = 0  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.bones: list[int] = [-1 for _ in range(16)]
        self.unknown1: int = 0  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.

        # Runtime data
        self.bonemap: list[int] = []
        self.tbones: list[Vector3] = []
        self.qbones: list[Vector4] = []

    def read(self, reader: BinaryReader) -> _SkinmeshHeader:
        """Read skinmesh header data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated skinmesh header instance.
        """
        super().read(reader)
        self.unknown2 = reader.read_int32()  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.unknown3 = reader.read_int32()  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.unknown4 = reader.read_int32()  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.offset_to_mdx_weights = reader.read_uint32()
        self.offset_to_mdx_bones = reader.read_uint32()
        self.offset_to_bonemap = reader.read_uint32()
        self.bonemap_count = reader.read_uint32()
        self.offset_to_qbones = reader.read_uint32()
        self.qbones_count = reader.read_uint32()
        self.qbones_count2 = reader.read_uint32()
        self.offset_to_tbones = reader.read_uint32()
        self.tbones_count = reader.read_uint32()
        self.tbones_count2 = reader.read_uint32()
        self.offset_to_unknown0 = reader.read_uint32()  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.unknown0_count = reader.read_uint32()  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.unknown0_count2 = reader.read_uint32()  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.bones = [reader.read_uint16() for _ in range(16)]
        self.unknown1 = reader.read_uint32()  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        return self

    def read_extra(self, reader: BinaryReader):
        """Read additional mesh data referenced by offsets.

        Args:
            reader: Binary reader to read data from.
        """
        super().read_extra(reader)
        reader.seek(self.offset_to_bonemap)
        self.bonemap = [reader.read_single() for _ in range(self.bonemap_count)]
        self.tbones = [reader.read_vector3() for _ in range(self.tbones_count)]
        self.qbones = [reader.read_vector4() for _ in range(self.qbones_count)]

    def write(self, writer: BinaryWriter, game: Game):
        """Write skinmesh header data to a binary stream.

        Args:
            writer: Binary writer to write data to.
            game: Game version (K1/K2) to determine format specifics.
        """
        super().write(writer, game)
        writer.write_int32(self.unknown2)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        writer.write_int32(self.unknown3)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        writer.write_int32(self.unknown4)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        writer.write_uint32(self.offset_to_mdx_weights)
        writer.write_uint32(self.offset_to_mdx_bones)
        writer.write_uint32(self.offset_to_bonemap)
        writer.write_uint32(self.bonemap_count)
        writer.write_uint32(self.offset_to_qbones)
        writer.write_uint32(self.qbones_count)
        writer.write_uint32(self.qbones_count2)
        writer.write_uint32(self.offset_to_tbones)
        writer.write_uint32(self.tbones_count)
        writer.write_uint32(self.tbones_count2)
        writer.write_uint32(self.offset_to_unknown0)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        writer.write_uint32(self.unknown0_count)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        writer.write_uint32(self.unknown0_count2)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        for i in range(16):
            writer.write_uint32(self.bones[i])
        writer.write_uint32(self.unknown1)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.

    def header_size(self, game: Game) -> int:
        """Get size of header for given game version.

        Args:
            game: Game version (K1/K2) to determine format specifics.

        Returns:
            int: Header size in bytes.
        """
        return _SkinmeshHeader.K1_SIZE if game == Game.K1 else _SkinmeshHeader.K2_SIZE
