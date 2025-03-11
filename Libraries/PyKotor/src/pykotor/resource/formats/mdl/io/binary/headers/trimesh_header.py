from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pykotor.common.misc import Game, ResRef
from utility.common.geometry import Vector2, Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter
    from pykotor.resource.formats.mdl.data.face import _Face


class _TrimeshHeader:
    """Header data for triangle mesh nodes.

    Contains all the metadata and data offsets needed to describe a triangle mesh,
    including vertices, faces, textures, and material properties.

    Attributes:
        function_pointer0 (int): First function pointer.
        function_pointer1 (int): Second function pointer.
        offset_to_faces (int): Offset to face data.
        faces_count (int): Number of faces.
        faces_count2 (int): Duplicate of faces_count for validation.
        bounding_box_min (Vector3): Minimum point of bounding box.
        bounding_box_max (Vector3): Maximum point of bounding box.
        radius (float): Bounding sphere radius.
        average (Vector3): Average vertex position.
        diffuse (Vector3): Diffuse color.
        ambient (Vector3): Ambient color.
        transparency_hint (int): Transparency settings.
        texture1 (str): Primary texture name.
        texture2 (str): Secondary texture name.
        texture_padding (bytes): Padding for texture data alignment.
        offset_to_indices_counts (int): Offset to indices count array.
        indices_counts_count (int): Number of indices counts.
        indices_counts_count2 (int): Duplicate of indices_counts_count.
        offset_to_indices_offset (int): Offset to indices offset array.
        indices_offsets_count (int): Number of indices offsets.
        indices_offsets_count2 (int): Duplicate of indices_offsets_count.
        offset_to_counters (int): Offset to counter array.
        counters_count (int): Number of counters.
        counters_count2 (int): Duplicate of counters_count.
        face_plane_flags (bytes): Face plane and material flags.
        saber_params (bytes): Lightsaber blade parameters.
        mesh_flags (int): Additional mesh rendering flags.
        uv_direction (Vector2): UV animation direction.
        uv_jitter (float): UV jitter amount.
        uv_speed (float): UV animation speed.
        mdx_data_size (int): Size of MDX vertex data block.
        mdx_data_bitmap (int): Flags indicating MDX data contents.
        mdx_vertex_offset (int): Offset to vertex positions in MDX.
        mdx_normal_offset (int): Offset to normal vectors in MDX.
        mdx_color_offset (int): Offset to vertex colors in MDX.
        mdx_texture1_offset (int): Offset to primary UVs in MDX.
        mdx_texture2_offset (int): Offset to secondary UVs in MDX.
        mdx_tangent_offset (int): Offset to tangent space data in MDX.
        mdx_weights_offset (int): Offset to bone weights in MDX (skinned meshes).
        mdx_indices_offset (int): Offset to bone indices in MDX (skinned meshes).
        mdx_extra1_offset (int): ???
        mdx_extra2_offset (int): ???
        mdx_extra3_offset (int): ???
        vertex_count (int): Number of vertices.
        texture_count (int): Number of textures used.
        has_lightmap (int): Whether mesh has lightmap.
        rotate_texture (int): Whether textures should rotate.
        background (int): Whether mesh is background geometry.
        has_shadow (int): Whether mesh casts shadows.
        beaming (int): Whether mesh has beaming effect.
        render (int): Whether mesh should be rendered.
        dirt_enabled (int): Whether dirt mapping is enabled.
        dirt_texture (ResRef): Dirt texture name.
        total_area (float): Total surface area.
        mdx_data_offset (int): Offset to MDX data block.
        vertices_offset (int): Offset to vertex data.
    """

    K1_SIZE: ClassVar[Literal[332]] = 0x14C
    """Size of the header in bytes for KotOR 1."""

    K2_SIZE: ClassVar[Literal[340]] = 0x154
    """Size of the header in bytes for KotOR 2."""

    K1_FUNCTION_POINTER0: ClassVar[Literal[4216656]] = 0x405750
    """Function pointer 0 for KotOR 1."""

    K2_FUNCTION_POINTER0: ClassVar[Literal[4216880]] = 0x405830
    """Function pointer 0 for KotOR 2."""

    K1_SKIN_FUNCTION_POINTER0: ClassVar[Literal[4216592]] = 0x405710
    """Skin function pointer 0 for KotOR 1."""

    K2_SKIN_FUNCTION_POINTER0: ClassVar[Literal[4216816]] = 0x4057F0
    """Skin function pointer 0 for KotOR 2."""

    K1_DANGLY_FUNCTION_POINTER0: ClassVar[Literal[4216640]] = 0x405740
    """Dangly function pointer 0 for KotOR 1."""

    K2_DANGLY_FUNCTION_POINTER0: ClassVar[Literal[4216864]] = 0x405820
    """Dangly function pointer 0 for KotOR 2."""

    K1_FUNCTION_POINTER1: ClassVar[Literal[4216672]] = 0x405760
    """Function pointer 1 for KotOR 1."""

    K2_FUNCTION_POINTER1: ClassVar[Literal[4216896]] = 0x405840
    """Function pointer 1 for KotOR 2."""

    K1_SKIN_FUNCTION_POINTER1: ClassVar[Literal[4216608]] = 0x405720
    """Skin function pointer 1 for KotOR 1."""

    K2_SKIN_FUNCTION_POINTER1: ClassVar[Literal[4216832]] = 0x405800
    """Skin function pointer 1 for KotOR 2."""

    K1_DANGLY_FUNCTION_POINTER1: ClassVar[Literal[4216624]] = 0x405730
    """Dangly function pointer 1 for KotOR 1."""

    K2_DANGLY_FUNCTION_POINTER1: ClassVar[Literal[4216848]] = 0x405810
    """Dangly function pointer 1 for KotOR 2."""

    def __init__(self):
        # Function pointers and basic mesh info
        self.function_pointer0: int = 0
        self.function_pointer1: int = 0
        self.offset_to_faces: int = 0
        self.faces_count: int = 0
        self.faces_count2: int = 0

        # Bounding geometry
        self.bounding_box_min: Vector3 = Vector3.from_null()
        self.bounding_box_max: Vector3 = Vector3.from_null()
        self.radius: float = 0.0
        self.average: Vector3 = Vector3.from_null()

        # Material properties
        self.diffuse: Vector3 = Vector3.from_null()
        self.ambient: Vector3 = Vector3.from_null()
        self.transparency_hint: int = 0
        self.texture1: ResRef = ResRef.from_blank()
        self.texture2: ResRef = ResRef.from_blank()
        self.texture_padding: bytes = b"\x00" * 24

        # Index and counter arrays
        self.offset_to_indices_counts: int = 0
        self.indices_counts_count: int = 0
        self.indices_counts_count2: int = 0
        self.offset_to_indices_offset: int = 0
        self.indices_offsets_count: int = 0
        self.indices_offsets_count2: int = 0
        self.offset_to_counters: int = 0
        self.counters_count: int = 0
        self.counters_count2: int = 0

        # Face and material flags
        self.face_plane_flags: bytes = b"\xff\xff\xff\xff" + b"\xff\xff\xff\xff" + b"\x00\x00\x00\x00"
        self.saber_params: list[int] = []
        self.mesh_flags: int = 0

        # UV animation
        self.uv_direction: Vector2 = Vector2.from_null()
        self.uv_jitter: float = 0.0
        self.uv_speed: float = 0.0

        # MDX data
        self.mdx_data_size: int = 0
        self.mdx_data_bitmap: int = 0
        self.mdx_vertex_offset: int = 0
        self.mdx_normal_offset: int = 0
        self.mdx_color_offset: int = 0xFFFFFFFF
        self.mdx_texture1_offset: int = 0
        self.mdx_texture2_offset: int = 0

        # MDX row offsets
        self.mdx_tangent_offset: int = 0xFFFFFFFF
        self.mdx_weights_offset: int = 0xFFFFFFFF
        self.mdx_indices_offset: int = 0xFFFFFFFF
        self.unknown_offset1: int = 0xFFFFFFFF  # TODO: What is this??
        self.unknown_offset2: int = 0xFFFFFFFF  # TODO: What is this??
        self.unknown_offset3: int = 0xFFFFFFFF  # TODO: What is this??

        # Mesh properties
        self.vertex_count: int = 0
        self.texture_count: int = 1
        self.has_lightmap: int = 0
        self.rotate_texture: int = 0
        self.background: int = 0
        self.has_shadow: int = 0
        self.beaming: int = 0
        self.render: int = 0

        # Dirt mapping
        self.dirt_enabled: int = 0
        self.dirt_texture: ResRef = ResRef.from_blank()

        # More unknown fields
        self.unknown9: int = 0  # TODO: What is this??
        self.unknown10: int = 0  # TODO: What is this??
        self.total_area: float = 0.0
        self.unknown11: int = 0  # TODO: What is this??
        self.unknown12: int = 0  # TODO: What is this??
        self.unknown13: int = 0  # TODO: What is this??

        # Data offsets
        self.mdx_data_offset: int = 0
        self.vertices_offset: int = 0

        # Runtime data
        self.faces: list[_Face] = []
        self.vertices: list[Vector3] = []
        self.indices_offsets: list[int] = []
        self.indices_counts: list[int] = []
        self.inverted_counters: list[int] = []

    def header_size(self, game: Game) -> int:
        """Get size of header for given game version.

        Args:
            game: Game version (K1/K2) to determine format specifics.

        Returns:
            int: Header size in bytes.
        """
        return _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE

    def faces_size(self) -> int:
        """Get total size of face data.

        Returns:
            int: Size in bytes.
        """
        from pykotor.resource.formats.mdl.io.face import _Face

        return len(self.faces) * _Face.SIZE

    def vertices_size(self) -> int:
        """Get total size of vertex data.

        Returns:
            int: Size in bytes.
        """
        return len(self.vertices) * 12  # 3 floats per vertex * 4 bytes per float

    def read(self, reader: BinaryReader) -> _TrimeshHeader:
        """Read trimesh header data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated trimesh header instance.
        """
        self.function_pointer0 = reader.read_uint32()
        self.function_pointer1 = reader.read_uint32()
        self.offset_to_faces = reader.read_uint32()
        self.faces_count = reader.read_uint32()
        self.faces_count2 = reader.read_uint32()
        self.bounding_box_min = reader.read_vector3()
        self.bounding_box_max = reader.read_vector3()
        self.radius = reader.read_single()
        self.average = reader.read_vector3()
        self.diffuse = reader.read_vector3()
        self.ambient = reader.read_vector3()
        self.transparency_hint = reader.read_uint32()
        self.texture1 = ResRef(reader.read_terminated_string("\0", 32))
        self.texture2 = ResRef(reader.read_terminated_string("\0", 32))
        self.texture_padding = reader.read_bytes(24)
        self.offset_to_indices_counts = reader.read_uint32()
        self.indices_counts_count = reader.read_uint32()
        self.indices_counts_count2 = reader.read_uint32()
        self.offset_to_indices_offset = reader.read_uint32()
        self.indices_offsets_count = reader.read_uint32()
        self.indices_offsets_count2 = reader.read_uint32()
        self.offset_to_counters = reader.read_uint32()
        self.counters_count = reader.read_uint32()
        self.counters_count2 = reader.read_uint32()
        self.face_plane_flags = reader.read_bytes(12)
        self.saber_params = [reader.read_uint8() for _ in range(8)]
        self.mesh_flags = reader.read_uint32()
        self.uv_direction = reader.read_vector2()
        self.uv_jitter = reader.read_single()
        self.uv_speed = reader.read_single()
        self.mdx_data_size = reader.read_uint32()
        self.mdx_data_bitmap = reader.read_uint32()
        self.mdx_vertex_offset = reader.read_uint32()
        self.mdx_normal_offset = reader.read_uint32()
        self.mdx_color_offset = reader.read_uint32()
        self.mdx_texture1_offset = reader.read_uint32()
        self.mdx_texture2_offset = reader.read_uint32()
        self.mdx_tangent_offset = reader.read_uint32()
        self.mdx_weights_offset = reader.read_uint32()
        self.mdx_indices_offset = reader.read_uint32()
        self.unknown_offset1 = reader.read_uint32()  # TODO: What is this??
        self.unknown_offset2 = reader.read_uint32()  # TODO: What is this??
        self.unknown_offset3 = reader.read_uint32()  # TODO: What is this??
        self.vertex_count = reader.read_uint16()
        self.texture_count = reader.read_uint16()
        self.has_lightmap = reader.read_uint8()
        self.rotate_texture = reader.read_uint8()
        self.background = reader.read_uint8()
        self.has_shadow = reader.read_uint8()
        self.beaming = reader.read_uint8()
        self.render = reader.read_uint8()
        self.unknown9 = reader.read_uint8()  # TODO: What is this??
        self.unknown10 = reader.read_uint8()  # TODO: What is this??
        self.total_area = reader.read_single()
        self.unknown11 = reader.read_uint32()  # TODO: What is this??
        if self.function_pointer0 in {
            _TrimeshHeader.K2_FUNCTION_POINTER0,
            _TrimeshHeader.K2_DANGLY_FUNCTION_POINTER0,
            _TrimeshHeader.K2_SKIN_FUNCTION_POINTER0,
        }:
            self.unknown12 = reader.read_uint32()  # TODO: What is this??
            self.unknown13 = reader.read_uint32()  # TODO: What is this??
        self.mdx_data_offset = reader.read_uint32()
        self.vertices_offset = reader.read_uint32()
        return self

    def read_extra(self, reader: BinaryReader):
        """Read additional mesh data referenced by offsets.

        Args:
            reader: Binary reader to read data from.
        """
        from pykotor.resource.formats.mdl.io.face import _Face

        reader.seek(self.vertices_offset)
        self.vertices = [reader.read_vector3() for _ in range(self.vertex_count)]

        reader.seek(self.offset_to_faces)
        self.faces = [_Face().read(reader) for _ in range(self.faces_count)]

    def write(self, writer: BinaryWriter, game: Game):
        """Write trimesh header data to a binary stream.

        Args:
            writer: Binary writer to write data to.
            game: Game version (K1/K2) to determine format specifics.
        """
        writer.write_uint32(self.function_pointer0)
        writer.write_uint32(self.function_pointer1)
        writer.write_uint32(self.offset_to_faces)
        writer.write_uint32(self.faces_count)
        writer.write_uint32(self.faces_count2)
        writer.write_vector3(self.bounding_box_min)
        writer.write_vector3(self.bounding_box_max)
        writer.write_single(self.radius)
        writer.write_vector3(self.average)
        writer.write_vector3(self.diffuse)
        writer.write_vector3(self.ambient)
        writer.write_uint32(self.transparency_hint)
        writer.write_string(str(self.texture1), string_length=32, encoding="ascii")
        writer.write_string(str(self.texture2), string_length=32, encoding="ascii")
        writer.write_bytes(self.texture_padding)
        writer.write_uint32(self.offset_to_indices_counts)
        writer.write_uint32(self.indices_counts_count)
        writer.write_uint32(self.indices_counts_count2)
        writer.write_uint32(self.offset_to_indices_offset)
        writer.write_uint32(self.indices_offsets_count)
        writer.write_uint32(self.indices_offsets_count2)
        writer.write_uint32(self.offset_to_counters)
        writer.write_uint32(self.counters_count)
        writer.write_uint32(self.counters_count2)
        writer.write_bytes(self.face_plane_flags)
        for param in self.saber_params:
            writer.write_uint8(param)
        writer.write_uint32(self.mesh_flags)
        writer.write_vector2(self.uv_direction)
        writer.write_single(self.uv_jitter)
        writer.write_single(self.uv_speed)
        writer.write_uint32(self.mdx_data_size)
        writer.write_uint32(self.mdx_data_bitmap)
        writer.write_uint32(self.mdx_vertex_offset)
        writer.write_uint32(self.mdx_normal_offset)
        writer.write_uint32(self.mdx_color_offset)
        writer.write_uint32(self.mdx_texture1_offset)
        writer.write_uint32(self.mdx_texture2_offset)
        writer.write_uint32(self.mdx_tangent_offset)
        writer.write_uint32(self.mdx_weights_offset)
        writer.write_uint32(self.mdx_indices_offset)
        writer.write_uint32(self.unknown_offset1)  # TODO: What is this??
        writer.write_uint32(self.unknown_offset2)  # TODO: What is this??
        writer.write_uint32(self.unknown_offset3)  # TODO: What is this??
        writer.write_uint16(self.vertex_count)
        writer.write_uint16(self.texture_count)
        writer.write_uint8(self.has_lightmap)
        writer.write_uint8(self.rotate_texture)
        writer.write_uint8(self.background)
        writer.write_uint8(self.has_shadow)
        writer.write_uint8(self.beaming)
        writer.write_uint8(self.render)
        writer.write_uint8(self.unknown9)  # TODO: What is this??
        writer.write_uint8(self.unknown10)  # TODO: What is this??
        writer.write_single(self.total_area)
        writer.write_uint32(self.unknown11)  # TODO: What is this??
        if game == Game.K2:
            writer.write_uint32(self.unknown12)  # TODO: What is this??
            writer.write_uint32(self.unknown13)  # TODO: What is this??
        writer.write_uint32(self.mdx_data_offset)
        writer.write_uint32(self.vertices_offset)
