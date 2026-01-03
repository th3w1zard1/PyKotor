from __future__ import annotations

import math
import os

from typing import TYPE_CHECKING, ClassVar, cast

from pykotor.common.misc import Color, Game
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.mdl.mdl_data import (
    MDL,
    MDLAnimation,
    MDLBoneVertex,
    MDLController,
    MDLControllerRow,
    MDLEvent,
    MDLFace,
    MDLMesh,
    MDLNode,
    MDLNodeFlags,
    MDLSkin,
    _mdl_recompute_mesh_face_payload,
)
from pykotor.resource.formats.mdl.mdl_types import MDLClassification, MDLControllerType, MDLNodeType
from utility.common.geometry import Vector2, Vector3, Vector4

# Debug logging: Enable via environment variable PYKOTOR_DEBUG_MDL=1
_DEBUG_MDL = os.environ.get("PYKOTOR_DEBUG_MDL", "").strip() in ("1", "true", "True", "TRUE", "yes", "Yes", "YES")

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.stream import BinaryWriterBytearray
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


# Fast-loading flags for render-only mode
MDL_FAST_LOAD_FLAGS = {
    "skip_controllers": True,
    "skip_animations": True,
    "minimal_mesh_data": True,
}


class _ModelHeader:
    SIZE: ClassVar[int] = 196

    def __init__(
        self,
    ):
        self.geometry: _GeometryHeader = _GeometryHeader()
        self.model_type: int = 0
        self.unknown0: int = 0  # TODO: what is this?
        self.padding0: int = 0
        self.fog: int = 0
        self.unknown1: int = 0  # TODO: what is this?
        self.offset_to_animations: int = 0
        self.animation_count: int = 0
        self.animation_count2: int = 0
        self.unknown2: int = 0  # TODO: what is this?
        self.bounding_box_min: Vector3 = Vector3.from_null()
        self.bounding_box_max: Vector3 = Vector3.from_null()
        self.radius: float = 0.0
        self.anim_scale: float = 0.0
        self.supermodel: str = ""
        self.offset_to_super_root: int = 0
        self.unknown3: int = 0  # Unknown field from Names array header (cchargin mdl_info.html). Second field after offset_to_super_root. Purpose unknown but preserved for format compatibility.
        self.mdx_size: int = 0
        self.mdx_offset: int = 0
        self.offset_to_name_offsets: int = 0
        self.name_offsets_count: int = 0
        self.name_offsets_count2: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _ModelHeader:
        self.geometry = _GeometryHeader().read(reader)
        self.model_type = reader.read_uint8()
        self.unknown0 = reader.read_uint8()  # TODO: what is this?
        self.padding0 = reader.read_uint8()
        self.fog = reader.read_uint8()
        self.unknown1 = reader.read_uint32()  # TODO: what is this?
        self.offset_to_animations = reader.read_uint32()
        self.animation_count = reader.read_uint32()
        self.animation_count2 = reader.read_uint32()
        self.unknown2 = reader.read_uint32()  # TODO: what is this?
        self.bounding_box_min = reader.read_vector3()
        self.bounding_box_max = reader.read_vector3()
        self.radius = reader.read_single()
        self.anim_scale = reader.read_single()
        self.supermodel = reader.read_terminated_string("\0", 32)
        self.offset_to_super_root = reader.read_uint32()
        self.unknown3 = (
            reader.read_uint32()
        )  # Unknown field from Names array header (cchargin mdl_info.html). Second field after offset_to_super_root. Purpose unknown but preserved for format compatibility.
        self.mdx_size = reader.read_uint32()
        self.mdx_offset = reader.read_uint32()
        self.offset_to_name_offsets = reader.read_uint32()
        self.name_offsets_count = reader.read_uint32()
        self.name_offsets_count2 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        self.geometry.write(writer)
        writer.write_uint8(self.model_type)
        writer.write_uint8(self.unknown0)
        writer.write_uint8(self.padding0)
        writer.write_uint8(self.fog)
        writer.write_uint32(self.unknown1)
        writer.write_uint32(self.offset_to_animations)
        writer.write_uint32(self.animation_count)
        writer.write_uint32(self.animation_count2)
        writer.write_uint32(self.unknown2)
        writer.write_vector3(self.bounding_box_min)
        writer.write_vector3(self.bounding_box_max)
        writer.write_single(self.radius)
        writer.write_single(self.anim_scale)
        writer.write_string(self.supermodel, string_length=32, encoding="ascii", errors="ignore")
        writer.write_uint32(self.offset_to_super_root)
        writer.write_uint32(
            self.unknown3
        )  # Unknown field from Names array header (cchargin mdl_info.html). Second field after offset_to_super_root. Purpose unknown but preserved for format compatibility.
        writer.write_uint32(self.mdx_size)
        writer.write_uint32(self.mdx_offset)
        writer.write_uint32(self.offset_to_name_offsets)
        writer.write_uint32(self.name_offsets_count)
        writer.write_uint32(self.name_offsets_count2)


class _GeometryHeader:
    SIZE = 80

    K1_FUNCTION_POINTER0 = 4273776
    K2_FUNCTION_POINTER0 = 4285200
    K1_ANIM_FUNCTION_POINTER0 = 4273392
    K2_ANIM_FUNCTION_POINTER0 = 4284816

    K1_FUNCTION_POINTER1 = 4216096
    K2_FUNCTION_POINTER1 = 4216320
    K1_ANIM_FUNCTION_POINTER1 = 4451552
    K2_ANIM_FUNCTION_POINTER1 = 4522928

    GEOM_TYPE_ROOT = 2
    GEOM_TYPE_ANIM = 5

    def __init__(
        self,
    ):
        self.function_pointer0: int = 0
        self.function_pointer1: int = 0
        self.model_name: str = ""
        self.root_node_offset: int = 0
        self.node_count: int = 0
        self.unknown0: bytes = b"\x00" * 28
        self.geometry_type: int = 0
        self.padding: bytes = b"\x00" * 3

    def read(
        self,
        reader: BinaryReader,
    ) -> _GeometryHeader:
        self.function_pointer0 = reader.read_uint32()
        self.function_pointer1 = reader.read_uint32()
        self.model_name = reader.read_terminated_string("\0", 32)
        self.root_node_offset = reader.read_uint32()
        self.node_count = reader.read_uint32()
        self.unknown0 = reader.read_bytes(28)
        self.geometry_type = reader.read_uint8()
        self.padding = reader.read_bytes(3)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint32(self.function_pointer0)
        writer.write_uint32(self.function_pointer1)
        writer.write_string(self.model_name, string_length=32, encoding="ascii")
        writer.write_uint32(self.root_node_offset)
        writer.write_uint32(self.node_count)
        writer.write_bytes(self.unknown0)
        writer.write_uint8(self.geometry_type)
        writer.write_bytes(self.padding)


class _AnimationHeader:
    SIZE = _GeometryHeader.SIZE + 56

    def __init__(
        self,
    ):
        self.geometry: _GeometryHeader = _GeometryHeader()
        self.duration: float = 0.0
        self.transition: float = 0.0
        self.root: str = ""
        self.offset_to_events: int = 0
        self.event_count: int = 0
        self.event_count2: int = 0
        self.unknown0: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _AnimationHeader:
        self.geometry = _GeometryHeader().read(reader)
        self.duration = reader.read_single()
        self.transition = reader.read_single()
        self.root = reader.read_terminated_string("\0", 32)
        self.offset_to_events = reader.read_uint32()
        self.event_count = reader.read_uint32()
        self.event_count2 = reader.read_uint32()
        self.unknown0 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        self.geometry.write(writer)
        writer.write_single(self.duration)
        writer.write_single(self.transition)
        writer.write_string(self.root, string_length=32, encoding="ascii")
        writer.write_uint32(self.offset_to_events)
        writer.write_uint32(self.event_count)
        writer.write_uint32(self.event_count2)
        writer.write_uint32(self.unknown0)


class _Animation:
    def __init__(
        self,
    ):
        self.header: _AnimationHeader = _AnimationHeader()
        self.events: list[_EventStructure] = []
        self.w_nodes: list[_Node] = []

    def read(
        self,
        reader: BinaryReader,
    ) -> _Animation:
        self.header = _AnimationHeader().read(reader)

        # read events
        return self

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ):
        self.header.write(writer)
        for event in self.events:
            event.write(writer)
        for node in self.w_nodes:
            node.write(writer, game)

    def events_offset(self) -> int:
        # Always after header
        return _AnimationHeader.SIZE

    def events_size(self) -> int:
        return _EventStructure.SIZE * len(self.events)

    def nodes_offset(self) -> int:
        """Returns offset of the first node relative to the start of the animation data."""
        # Always after events
        return self.events_offset() + self.events_size()

    def nodes_size(self):
        return sum(node.calc_size(Game.K1) for node in self.w_nodes)

    def size(self) -> int:
        return self.nodes_offset() + self.nodes_size()


class _EventStructure:
    SIZE = 36

    def __init__(self):
        self.activation_time: float = 0.0
        self.event_name: str = ""

    def read(
        self,
        reader: BinaryReader,
    ) -> _EventStructure:
        self.activation_time = reader.read_single()
        self.event_name = reader.read_terminated_string("\0", 32)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_single(self.activation_time)
        writer.write_string(self.event_name, string_length=32, encoding="ascii")


class _Controller:
    SIZE = 16

    def __init__(self):
        self.type_id: int = 0
        self.unknown0: int = 0xFFFF
        self.row_count: int = 0
        self.key_offset: int = 0
        self.data_offset: int = 0
        self.column_count: int = 0
        self.unknown1: bytes = b"\x00" * 3

    def read(
        self,
        reader: BinaryReader,
    ) -> _Controller:
        self.type_id = reader.read_uint32()
        self.unknown0 = reader.read_uint16()
        self.row_count = reader.read_uint16()
        self.key_offset = reader.read_uint16()
        self.data_offset = reader.read_uint16()
        self.column_count = reader.read_uint8()
        self.unknown1 = reader.read_bytes(3)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint32(self.type_id)
        writer.write_uint16(self.unknown0)
        writer.write_uint16(self.row_count)
        writer.write_uint16(self.key_offset)
        writer.write_uint16(self.data_offset)
        writer.write_uint8(self.column_count)
        writer.write_bytes(self.unknown1)


class _Node:
    SIZE: ClassVar[int] = 80

    """
    Ordering:
        # Node Header
        # Trimesh Header
        # ...
        # Face indices count array
        # Face indices offset array
        # Faces
        # Vertices
        # Inverted counter array
        # Children
        # Controllers
        # Controller Data
    """

    def __init__(
        self,
    ):
        self.header: _NodeHeader | None = _NodeHeader()
        self.trimesh: _TrimeshHeader | None = None
        self.skin: _SkinmeshHeader | None = None
        self.light: _LightHeader | None = None
        self.emitter: _EmitterHeader | None = None
        self.reference: _ReferenceHeader | None = None
        self.children_offsets: list[int] = []

        self.w_children = []
        self.w_controllers: list[_Controller] = []
        self.w_controller_data: list[float] = []

    def read(
        self,
        reader: BinaryReader,
        game: Game,
    ) -> _Node:
        self.header = _NodeHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.MESH:
            self.trimesh = _TrimeshHeader().read(reader, game)

        if self.header.type_id & MDLNodeFlags.SKIN:
            self.skin = _SkinmeshHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.LIGHT:
            self.light = _LightHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.EMITTER:
            self.emitter = _EmitterHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.REFERENCE:
            self.reference = _ReferenceHeader().read(reader)

        if self.trimesh:
            self.trimesh.read_extra(reader)
        if self.skin:
            self.skin.read_extra(reader)

        # Validate children_count and offset_to_children before reading
        # If offset_to_children is invalid (0xFFFFFFFF) or out of bounds, or children_count is suspiciously large,
        # set children_count to 0 to prevent reading garbage data
        if (
            self.header.offset_to_children == 0xFFFFFFFF
            or self.header.offset_to_children >= reader.size()
            or self.header.children_count > 0x7FFFFFFF  # Prevent negative values when interpreted as signed
            or self.header.children_count * 4 + self.header.offset_to_children > reader.size()
        ):
            self.header.children_count = 0
            self.header.children_count2 = 0
            self.children_offsets = []
        else:
            try:
                reader.seek(self.header.offset_to_children)
                self.children_offsets = [reader.read_uint32() for _ in range(self.header.children_count)]
            except Exception:
                # If reading fails, set to empty to prevent corruption
                self.header.children_count = 0
                self.header.children_count2 = 0
                self.children_offsets = []
        return self

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ):
        assert self.header is not None
        self.header.write(writer)

        if self.trimesh:
            self.trimesh.write(writer, game)

        if self.skin:
            self.skin.write(writer)

        if self.light:
            self.light.write(writer)

        if self.emitter:
            self.emitter.write(writer)

        if self.reference:
            self.reference.write(writer)

        if self.trimesh:
            self._write_trimesh_data(writer)
        if self.skin:
            self._write_skin_extra(writer)
        for child_offset in self.children_offsets:
            writer.write_uint32(child_offset)

        for controller in self.w_controllers:
            controller.write(writer)

        # Write controller data - compressed quaternions need special handling
        # Compressed quaternions are stored as uint32s, not floats
        # We need to iterate through controllers to identify which data entries are compressed quaternions
        data_idx = 0
        for controller in self.w_controllers:
            # Write time keys (floats)
            for _ in range(controller.row_count):
                if data_idx < len(self.w_controller_data):
                    writer.write_single(self.w_controller_data[data_idx])
                    data_idx += 1
            # Write data values
            # Check if this is a compressed quaternion controller (type 20, column_count 2)
            is_compressed_quat = (
                controller.type_id == int(MDLControllerType.ORIENTATION)
                and controller.column_count == 2
            )
            if is_compressed_quat:
                # Compressed quaternions: write as uint32s (2 floats per row: compressed uint32 + padding)
                for _ in range(controller.row_count):
                    if data_idx < len(self.w_controller_data):
                        # Convert float back to uint32 for compressed quaternion
                        compressed_uint32 = int(self.w_controller_data[data_idx])
                        writer.write_uint32(compressed_uint32)
                        data_idx += 1
                    if data_idx < len(self.w_controller_data):
                        # Padding float (should be 0.0)
                        writer.write_single(self.w_controller_data[data_idx])
                        data_idx += 1
            else:
                # Regular controller data: write as floats
                # Calculate number of floats per row from column_count
                # Bezier flag is encoded in bit 4 (0x10) of column_count
                is_bezier = bool(controller.column_count & 0x10)
                floats_per_row = controller.column_count & ~0x10  # Strip bezier flag if present
                if is_bezier:
                    # Bezier controllers: 3 floats per column
                    floats_per_row = floats_per_row * 3
                for _ in range(controller.row_count):
                    for _ in range(floats_per_row):
                        if data_idx < len(self.w_controller_data):
                            writer.write_single(self.w_controller_data[data_idx])
                            data_idx += 1

        if len(self.children_offsets) != self.header.children_count:
            msg = f"Number of child offsets in array does not match header count in {self.header.name_id} ({len(self.children_offsets)} vs {self.header.children_count})."
            raise ValueError(msg)

    def _write_trimesh_data(self, writer: BinaryWriter):
        assert self.trimesh is not None
        # Write indices counts array
        for count in self.trimesh.indices_counts:
            writer.write_uint32(count)

        # Write indices offsets array
        for offset in self.trimesh.indices_offsets:
            writer.write_uint32(offset)

        # Write inverted counters array (array3)
        for counter in self.trimesh.inverted_counters:
            writer.write_uint32(counter)

        # Write faces (full _Face structs)
        for face in self.trimesh.faces:
            face.write(writer)

        # Write vertices (Vector3 array)
        for vertex in self.trimesh.vertices:
            writer.write_vector3(vertex)

    def _write_skin_extra(self, writer: BinaryWriter) -> None:
        """Write variable-length skin blocks referenced by _SkinmeshHeader offsets."""
        assert self.skin is not None
        # Layout we write (immediately after trimesh vertex array):
        #   bonemap (float32 * count)
        #   qbones  (Vector4 * count)
        #   tbones  (Vector3 * count)
        #   unknown0 (float32 * count) [currently unused]
        if self.skin.bonemap_count and self.skin.bonemap:
            for v in self.skin.bonemap[: self.skin.bonemap_count]:
                writer.write_single(float(v))
        if self.skin.qbones_count and self.skin.qbones:
            for q in self.skin.qbones[: self.skin.qbones_count]:
                writer.write_vector4(q)
        if self.skin.tbones_count and self.skin.tbones:
            for t in self.skin.tbones[: self.skin.tbones_count]:
                writer.write_vector3(t)
        if self.skin.unknown0_count:
            # Not currently modeled; write zeros to match declared count.
            for _ in range(int(self.skin.unknown0_count)):
                writer.write_single(0.0)

    def all_headers_size(
        self,
        game: Game,
    ) -> int:
        size = _Node.SIZE
        if self.trimesh:
            size += _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE
        if self.skin:
            size += _SkinmeshHeader.SIZE
        if self.light:
            # Light header size: 15 uint32s (offsets/counts) + 1 float (flare_radius) + 7 uint32s (light properties) = 92 bytes
            size += 92
        if self.emitter:
            # Emitter header size: 3 floats + 1 uint32 + 1 float + 1 Vector2 + 5*32-byte strings + 4 uint32s + 1 uint8 + 3 padding + 1 uint32 = 212 bytes
            size += 212
        if self.reference:
            # Reference header size: 32-byte string + 1 uint32 = 36 bytes
            size += 36
        return size

    def indices_counts_offset(
        self,
        game: Game,
    ) -> int:
        return self.all_headers_size(game)

    def indices_offsets_offset(
        self,
        game: Game,
    ) -> int:
        offset = self.indices_counts_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.indices_counts) * 4
        return offset

    def inverted_counters_offset(
        self,
        game: Game,
    ) -> int:
        offset = self.indices_offsets_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.indices_offsets) * 4
        return offset

    def indices_offset(
        self,
        game: Game,
    ) -> int:
        offset = self.inverted_counters_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.inverted_counters) * 4
        return offset

    def vertices_offset(
        self,
        game: Game,
    ) -> int:
        # Vertices follow the face struct array.
        offset = self.faces_offset(game)
        if self.trimesh:
            offset += self.trimesh.faces_size()
        return offset

    def faces_offset(
        self,
        game: Game,
    ) -> int:
        # Faces begin immediately after all headers / index tables.
        # (Index tables are currently treated as optional and may be empty.)
        return self.indices_offset(game)

    def children_offsets_offset(
        self,
        game: Game,
    ) -> int:
        # Children offsets follow the vertex array and any skin extra blocks (bonemap/qbones/tbones).
        size = self.vertices_offset(game)
        if self.trimesh:
            size += self.trimesh.vertices_size()
        if self.skin:
            size += self.skin_extra_size()
        return size

    def children_offsets_size(
        self,
    ) -> int:
        assert self.header is not None
        return 4 * self.header.children_count

    def controllers_offset(
        self,
        game: Game,
    ) -> int:
        return self.children_offsets_offset(game) + self.children_offsets_size()

    def controllers_size(
        self,
    ) -> int:
        return _Controller.SIZE * len(self.w_controllers)

    def controller_data_offset(
        self,
        game: Game,
    ) -> int:
        return self.controllers_offset(game) + self.controllers_size()

    def controller_data_size(
        self,
    ) -> int:
        return len(self.w_controller_data) * 4

    def skin_extra_size(self) -> int:
        """Size of variable-length skin payload blocks written after vertices (MDL, not MDX)."""
        if not self.skin:
            return 0
        bonemap_bytes = int(self.skin.bonemap_count) * 4
        qbones_bytes = int(self.skin.qbones_count) * 16
        tbones_bytes = int(self.skin.tbones_count) * 12
        # unknown0 block currently not modeled; keep stable at 0 unless counts are set.
        unknown0_bytes = int(self.skin.unknown0_count) * 4
        return bonemap_bytes + qbones_bytes + tbones_bytes + unknown0_bytes

    def calc_size(
        self,
        game: Game,
    ) -> int:
        return self.controller_data_offset(game) + self.controller_data_size()


class _NodeHeader:
    SIZE = 80

    def __init__(
        self,
    ):
        self.type_id: int = 1
        self.name_id: int = 0
        self.node_id: int = 0
        self.padding0: int = 0
        self.offset_to_root: int = 0
        self.offset_to_parent: int = 0
        self.position: Vector3 = Vector3.from_null()
        self.orientation: Vector4 = Vector4.from_null()
        self.offset_to_children: int = 0
        self.children_count: int = 0
        self.children_count2: int = 0
        self.offset_to_controllers: int = 0
        self.controller_count: int = 0
        self.controller_count2: int = 0
        self.offset_to_controller_data: int = 0
        self.controller_data_length: int = 0
        self.controller_data_length2: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _NodeHeader:
        self.type_id = reader.read_uint16()
        self.node_id = reader.read_uint16()
        self.name_id = reader.read_uint16()
        self.padding0 = reader.read_uint16()
        self.offset_to_root = reader.read_uint32()
        self.offset_to_parent = reader.read_uint32()
        self.position = reader.read_vector3()
        self.orientation.w = reader.read_single()
        self.orientation.x = reader.read_single()
        self.orientation.y = reader.read_single()
        self.orientation.z = reader.read_single()
        self.offset_to_children = reader.read_uint32()
        # Clamp children_count to prevent Perl from interpreting it as negative (values >= 2^31)
        # MDLOps reads this as a signed integer, so we must ensure it's < 2^31
        children_count_raw = reader.read_uint32()
        if children_count_raw > 0x7FFFFFFF:
            children_count_raw = 0x7FFFFFFF
        self.children_count = children_count_raw
        self.children_count2 = children_count_raw
        self.offset_to_controllers = reader.read_uint32()
        self.controller_count = reader.read_uint32()
        self.controller_count2 = reader.read_uint32()
        self.offset_to_controller_data = reader.read_uint32()
        self.controller_data_length = reader.read_uint32()
        self.controller_data_length2 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint16(self.type_id)
        writer.write_uint16(self.node_id)
        writer.write_uint16(self.name_id)
        writer.write_uint16(self.padding0)
        writer.write_uint32(self.offset_to_root)
        writer.write_uint32(self.offset_to_parent)
        writer.write_vector3(self.position)
        writer.write_single(self.orientation.w)
        writer.write_single(self.orientation.x)
        writer.write_single(self.orientation.y)
        writer.write_single(self.orientation.z)
        writer.write_uint32(self.offset_to_children)
        writer.write_uint32(self.children_count)
        writer.write_uint32(self.children_count2)
        writer.write_uint32(self.offset_to_controllers)
        writer.write_uint32(self.controller_count)
        writer.write_uint32(self.controller_count2)
        writer.write_uint32(self.offset_to_controller_data)
        writer.write_uint32(self.controller_data_length)
        writer.write_uint32(self.controller_data_length2)


class _MDXDataFlags:
    VERTEX: Literal[0x0001] = 0x0001
    TEXTURE1: Literal[0x0002] = 0x0002
    TEXTURE2: Literal[0x0004] = 0x0004
    NORMAL: Literal[0x0020] = 0x0020
    BUMPMAP: Literal[0x0080] = 0x0080


class _TrimeshHeader:
    # NOTE: These sizes reflect the actual number of bytes written/read by `_TrimeshHeader.write/read`.
    # Historically these constants were out-of-sync, which caused MDLBinaryWriter node offset drift
    # (bad child offsets, OOB seeks) during roundtrips.
    K1_SIZE: Literal[361] = 361
    K2_SIZE: Literal[377] = 377

    K1_FUNCTION_POINTER0: Literal[4216656] = 4216656
    K2_FUNCTION_POINTER0: Literal[4216880] = 4216880
    K1_SKIN_FUNCTION_POINTER0: Literal[4216592] = 4216592
    K2_SKIN_FUNCTION_POINTER0: Literal[4216816] = 4216816
    K1_DANGLY_FUNCTION_POINTER0: Literal[4216640] = 4216640
    K2_DANGLY_FUNCTION_POINTER0: Literal[4216864] = 4216864

    K1_FUNCTION_POINTER1: Literal[4216672] = 4216672
    K2_FUNCTION_POINTER1: Literal[4216896] = 4216896
    K1_SKIN_FUNCTION_POINTER1: Literal[4216608] = 4216608
    K2_SKIN_FUNCTION_POINTER1: Literal[4216832] = 4216832
    K1_DANGLY_FUNCTION_POINTER1: Literal[4216624] = 4216624
    K2_DANGLY_FUNCTION_POINTER1: Literal[4216848] = 4216848

    def __init__(
        self,
    ):
        self.function_pointer0: int = 0
        self.function_pointer1: int = 0
        self.offset_to_faces: int = 0
        self.faces_count: int = 0
        self.faces_count2: int = 0
        self.bounding_box_min: Vector3 = Vector3.from_null()
        self.bounding_box_max: Vector3 = Vector3.from_null()
        self.radius: float = 0.0
        self.average: Vector3 = Vector3.from_null()
        self.diffuse: Vector3 = Vector3.from_null()
        self.ambient: Vector3 = Vector3.from_null()
        self.transparency_hint: int = 0
        self.texture1: str = ""
        self.texture2: str = ""
        self.unknown0: bytes = b"\x00" * 24  # TODO: what is this?
        self.offset_to_indices_counts: int = 0
        self.indices_counts_count: int = 0
        self.indices_counts_count2: int = 0
        self.offset_to_indices_offset: int = 0
        self.indices_offsets_count: int = 0
        self.indices_offsets_count2: int = 0
        self.offset_to_counters: int = 0
        self.counters_count: int = 0
        self.counters_count2: int = 0
        self.unknown1: bytes = b"\xff\xff\xff\xff" + b"\xff\xff\xff\xff" + b"\x00\x00\x00\x00"  # TODO: what is this?
        self.saber_unknowns: bytes = b"\x00" * 8  # TODO: what is this?
        self.unknown2: int = 0  # TODO: what is this?
        self.uv_direction: Vector2 = Vector2.from_null()
        self.uv_jitter: float = 0.0
        self.uv_speed: float = 0.0
        self.mdx_data_size: int = 0
        self.mdx_data_bitmap: int = 0
        self.mdx_vertex_offset: int = 0  # Offset to vertex data in MDX (0x0001 bitmap flag)
        self.mdx_normal_offset: int = 0  # Offset to normal data in MDX (0x0020 bitmap flag)
        self.mdx_color_offset: int = 0xFFFFFFFF  # Offset to color data in MDX (not used in bitmap)
        self.mdx_texture1_offset: int = 0  # Offset to primary UV data in MDX (0x0002 bitmap flag)
        self.mdx_texture2_offset: int = 0  # Offset to secondary UV data in MDX (0x0004 bitmap flag)
        self.mdx_unknown_offset: int = 0xFFFFFFFF  # Offset to unknown data in MDX (always -1)
        self.mdx_uv3_offset: int = 0xFFFFFFFF  # Offset to tertiary UV data in MDX (always -1)
        self.mdx_uv4_offset: int = 0xFFFFFFFF  # Offset to quaternary UV data in MDX (always -1)
        self.mdx_tangent_offset: int = 0xFFFFFFFF  # Offset to tangent/binormal data in MDX (36 bytes, weighted normals)
        self.mdx_unused_struct1_offset: int = 0xFFFFFFFF  # Offset to unused MDX structure 1 (always -1)
        self.mdx_unused_struct2_offset: int = 0xFFFFFFFF  # Offset to unused MDX structure 2 (always -1)
        self.mdx_unused_struct3_offset: int = 0xFFFFFFFF  # Offset to unused MDX structure 3 (always -1)
        self.vertex_count: int = 0
        self.texture_count: int = 1
        self.has_lightmap: int = 0
        self.rotate_texture: int = 0
        self.background: int = 0
        self.has_shadow: int = 0
        self.beaming: int = 0
        self.render: int = 0
        self.dirt_enabled: int = 0
        self.dirt_texture: str = ""
        self.unknown9: int = 0  # TODO: what is this?
        self.dirt_coordinate_space: int = 0  # UV coordinate space for dirt texture overlay
        self.total_area: float = 0.0
        self.unknown11: int = 0  # Reserved field (part of L[3] sequence after total_area) - always 0
        self.unknown12: int = 0  # Reserved field (K2 only, part of L[3] sequence after total_area) - always 0
        self.unknown13: int = 0  # Reserved field (K2 only, part of L[3] sequence after total_area) - always 0
        self.mdx_data_offset: int = 0
        self.vertices_offset: int = 0

        self.faces: list[_Face] = []
        self.vertices: list[Vector3] = []
        self.indices_offsets: list[int] = []
        self.indices_counts: list[int] = []
        self.inverted_counters: list[int] = []

    def read(
        self,
        reader: BinaryReader,
        game: Game,
    ) -> _TrimeshHeader:
        start_pos = reader.position()
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
        self.texture1 = reader.read_terminated_string("\0", 32)
        self.texture2 = reader.read_terminated_string("\0", 32)
        self.unknown0 = reader.read_bytes(24)  # TODO: what is this?
        self.offset_to_indices_counts = reader.read_uint32()
        self.indices_counts_count = reader.read_uint32()
        self.indices_counts_count2 = reader.read_uint32()
        self.offset_to_indices_offset = reader.read_uint32()
        self.indices_offsets_count = reader.read_uint32()
        self.indices_offsets_count2 = reader.read_uint32()
        self.offset_to_counters = reader.read_uint32()
        self.counters_count = reader.read_uint32()
        self.counters_count2 = reader.read_uint32()
        self.unknown1 = reader.read_bytes(12)  # -1 -1 0  TODO: what is this?
        self.saber_unknowns = reader.read_bytes(8)  # 3 0 0 0 0 0 0 0 TODO: what is this?
        self.unknown2 = reader.read_uint32()  # TODO: what is this?
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
        self.mdx_unknown_offset = reader.read_uint32()  # Offset to unknown data in MDX (always -1)
        self.mdx_uv3_offset = reader.read_uint32()  # Offset to tertiary UV data in MDX (always -1)
        self.mdx_uv4_offset = reader.read_uint32()  # Offset to quaternary UV data in MDX (always -1)
        self.mdx_tangent_offset = reader.read_uint32()  # Offset to tangent/binormal data in MDX (36 bytes, weighted normals)
        # K2 adds two extra u32s here (total +8 bytes) which accounts for K2_SIZE - K1_SIZE.
        self.mdx_unused_struct1_offset = reader.read_uint32()  # Offset to unused MDX structure 1 (often -1)
        if game == Game.K2:
            self.mdx_unused_struct2_offset = reader.read_uint32()  # Offset to unused MDX structure 2 (often -1)
            self.mdx_unused_struct3_offset = reader.read_uint32()  # Offset to unused MDX structure 3 (often -1)
        else:
            self.mdx_unused_struct2_offset = 0xFFFFFFFF
            self.mdx_unused_struct3_offset = 0xFFFFFFFF
        self.vertex_count = reader.read_uint16()
        self.texture_count = reader.read_uint16()
        self.has_lightmap = reader.read_uint8()
        self.rotate_texture = reader.read_uint8()
        self.background = reader.read_uint8()
        self.has_shadow = reader.read_uint8()
        self.beaming = reader.read_uint8()
        self.render = reader.read_uint8()
        self.dirt_enabled = reader.read_uint8()  # Dirt/weathering overlay texture enabled
        self.dirt_texture = reader.read_terminated_string("\0", 32)  # Dirt texture name
        self.unknown9 = reader.read_uint8()  # TODO: what is this?
        self.dirt_coordinate_space = reader.read_uint8()  # UV coordinate space for dirt texture overlay
        self.total_area = reader.read_single()
        self.unknown11 = reader.read_uint32()  # Reserved field (part of L[3] sequence after total_area) - always 0
        # Trimesh header size differs between K1 and K2 by +8 bytes.
        # Use the model's game version (from the file header) rather than volatile function pointers.
        if game == Game.K2:
            self.unknown12 = reader.read_uint32()  # Reserved (K2 only) - usually 0
            self.unknown13 = reader.read_uint32()  # Reserved (K2 only) - usually 0
        self.mdx_data_offset = reader.read_uint32()
        self.vertices_offset = reader.read_uint32()

        # Some real-world K1 files have tail fields at alternative fixed offsets.
        # Try to recover ONLY when the sequentially-read vertices_offset/count look invalid.
        if game == Game.K1:
            end_pos = reader.position()

            def _valid(vc: int, vo: int) -> bool:
                if vo in (0, 0xFFFFFFFF):
                    return False
                if vc < 0 or vc > 1_000_000:
                    return False
                needed = vc * 12
                return vo <= reader.size() and (vo + needed) <= reader.size()

            def _try_offsets(off_vc: int, off_mdx: int) -> tuple[int, int, int, int]:
                reader.seek(start_pos + off_vc)
                vc = reader.read_uint16()
                tc = reader.read_uint16()
                reader.seek(start_pos + off_mdx)
                mo = reader.read_uint32()
                vo = reader.read_uint32()
                return vc, tc, mo, vo

            # Only run recovery if vertex_count is invalid AND vertices are not in MDX
            # If mdx_data_offset is valid, vertices are in MDX, so vertices_offset being 0/0xFFFFFFFF is expected
            # Also run recovery if vertex_count is suspiciously low (0 or 1) - this is almost always wrong for meshes
            mdx_valid = self.mdx_data_offset not in (0, 0xFFFFFFFF) and self.mdx_data_offset <= reader.size()
            vertex_count_invalid = self.vertex_count < 0 or self.vertex_count > 1_000_000
            vertex_count_suspicious = self.vertex_count <= 1  # 0 or 1 is suspicious for a mesh with geometry

            if vertex_count_invalid or vertex_count_suspicious or (not _valid(int(self.vertex_count), int(self.vertices_offset)) and not mdx_valid):
                # Prefer the legacy MDLOps-style offsets first, then our writer's layout.
                for off_vc, off_mdx in ((304, 324), (300, 352)):
                    vc, tc, mo, vo = _try_offsets(off_vc, off_mdx)
                    # Reject recovered values that are suspiciously low (0 or 1) unless we can verify they're correct
                    # A vertex_count of 1 is almost always wrong for a mesh with geometry
                    if _valid(int(vc), int(vo)) and vc > 1:
                        self.vertex_count = vc
                        self.texture_count = tc
                        self.mdx_data_offset = mo
                        self.vertices_offset = vo
                        break
                    elif _valid(int(vc), int(vo)) and vc == 1:
                        # vertex_count of 1 is suspicious - never use it, even if original is invalid
                        # A vertex_count of 1 is almost always wrong for a mesh with geometry
                        # Continue to look for better alternatives
                        continue

            reader.seek(end_pos)
        return self

    def read_extra(
        self,
        reader: BinaryReader,
    ):
        # Indices counts array
        if self.offset_to_indices_counts not in (0, 0xFFFFFFFF) and self.indices_counts_count > 0:
            counts_bytes = self.indices_counts_count * 4  # uint32 per count
            if self.offset_to_indices_counts <= reader.size() and (self.offset_to_indices_counts + counts_bytes) <= reader.size():
                reader.seek(self.offset_to_indices_counts)
                self.indices_counts = [reader.read_uint32() for _ in range(self.indices_counts_count)]

        # Indices offsets array
        if self.offset_to_indices_offset not in (0, 0xFFFFFFFF) and self.indices_offsets_count > 0:
            offsets_bytes = self.indices_offsets_count * 4  # uint32 per offset
            if self.offset_to_indices_offset <= reader.size() and (self.offset_to_indices_offset + offsets_bytes) <= reader.size():
                reader.seek(self.offset_to_indices_offset)
                self.indices_offsets = [reader.read_uint32() for _ in range(self.indices_offsets_count)]

        # Inverted counters (array3) - read from offset_to_counters when counters_count > 0
        if self.offset_to_counters not in (0, 0xFFFFFFFF) and self.counters_count > 0:
            counters_bytes = self.counters_count * 4  # uint32 per counter
            if self.offset_to_counters <= reader.size() and (self.offset_to_counters + counters_bytes) <= reader.size():
                reader.seek(self.offset_to_counters)
                self.inverted_counters = [reader.read_uint32() for _ in range(self.counters_count)]

        # Faces
        if self.offset_to_faces not in (0, 0xFFFFFFFF) and self.faces_count > 0:
            faces_bytes = self.faces_count * _Face.SIZE
            if self.offset_to_faces <= reader.size() and (self.offset_to_faces + faces_bytes) <= reader.size():
                reader.seek(self.offset_to_faces)
                self.faces = [_Face().read(reader) for _ in range(self.faces_count)]

        # Vertices
        if self.vertices_offset not in (0, 0xFFFFFFFF) and self.vertex_count > 0:
            vertices_bytes = self.vertex_count * 12  # Vector3 of floats
            if self.vertices_offset <= reader.size() and (self.vertices_offset + vertices_bytes) <= reader.size():
                reader.seek(self.vertices_offset)
                self.vertices = [reader.read_vector3() for _ in range(self.vertex_count)]

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ):
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
        writer.write_string(self.texture1, string_length=32, encoding="ascii")
        writer.write_string(self.texture2, string_length=32, encoding="ascii")
        writer.write_bytes(self.unknown0)  # TODO: what is this?
        writer.write_uint32(self.offset_to_indices_counts)
        writer.write_uint32(self.indices_counts_count)
        writer.write_uint32(self.indices_counts_count2)
        writer.write_uint32(self.offset_to_indices_offset)
        writer.write_uint32(self.indices_offsets_count)
        writer.write_uint32(self.indices_offsets_count2)
        writer.write_uint32(self.offset_to_counters)
        writer.write_uint32(self.counters_count)
        writer.write_uint32(self.counters_count2)
        writer.write_bytes(self.unknown1)  # TODO: what is this?
        writer.write_bytes(self.saber_unknowns)  # TODO: what is this?
        writer.write_uint32(self.unknown2)  # TODO: what is this?
        writer.write_vector2(self.uv_direction)
        writer.write_single(self.uv_jitter)
        writer.write_single(self.uv_speed)
        writer.write_uint32(self.mdx_data_size)
        if _DEBUG_MDL:
            print(
                f"DEBUG _TrimeshHeader.write: texture1={self.texture1} bitmap=0x{self.mdx_data_bitmap:08X} TEXTURE1={bool(self.mdx_data_bitmap & _MDXDataFlags.TEXTURE1)} texture1_offset={self.mdx_texture1_offset}"
            )
            pos_before = writer.position()
            print(f"DEBUG _TrimeshHeader.write: Writing mdx_data_bitmap at position {pos_before}")
        writer.write_uint32(self.mdx_data_bitmap)
        writer.write_uint32(self.mdx_vertex_offset)
        writer.write_uint32(self.mdx_normal_offset)
        writer.write_uint32(self.mdx_color_offset)
        if _DEBUG_MDL and self.texture1:
            print(f"DEBUG _TrimeshHeader.write: About to write mdx_texture1_offset={self.mdx_texture1_offset} (type={type(self.mdx_texture1_offset)})")
        writer.write_uint32(self.mdx_texture1_offset)
        if _DEBUG_MDL:
            import struct

            _pos_after = writer.position()
            # Read back what we just wrote
            if hasattr(writer, "data") and callable(getattr(writer, "data", None)):
                data = writer.data()
                if pos_before + 20 <= len(data):
                    bitmap_written = struct.unpack("<I", data[pos_before : pos_before + 4])[0]
                    vertex_off_written = struct.unpack("<I", data[pos_before + 4 : pos_before + 8])[0]
                    _normal_off_written = struct.unpack("<I", data[pos_before + 8 : pos_before + 12])[0]
                    _color_off_written = struct.unpack("<I", data[pos_before + 12 : pos_before + 16])[0]
                    tex1_off_written = struct.unpack("<I", data[pos_before + 16 : pos_before + 20])[0]
                    print(
                        f"DEBUG _TrimeshHeader.write: Verified - bitmap=0x{bitmap_written:08X} (expected 0x{self.mdx_data_bitmap:08X}) vertex_off={vertex_off_written} (expected {self.mdx_vertex_offset}) tex1_off={tex1_off_written} (expected {self.mdx_texture1_offset})"
                    )
        writer.write_uint32(self.mdx_texture2_offset)
        writer.write_uint32(self.mdx_unknown_offset)  # Offset to unknown data in MDX (always -1)
        writer.write_uint32(self.mdx_uv3_offset)  # Offset to tertiary UV data in MDX (always -1)
        writer.write_uint32(self.mdx_uv4_offset)  # Offset to quaternary UV data in MDX (always -1)
        writer.write_uint32(self.mdx_tangent_offset)  # Offset to tangent/binormal data in MDX (36 bytes, weighted normals)
        writer.write_uint32(self.mdx_unused_struct1_offset)  # Offset to unused MDX structure 1 (often -1)
        if game == Game.K2:
            writer.write_uint32(self.mdx_unused_struct2_offset)  # Offset to unused MDX structure 2 (often -1)
            writer.write_uint32(self.mdx_unused_struct3_offset)  # Offset to unused MDX structure 3 (often -1)
        writer.write_uint16(self.vertex_count)
        writer.write_uint16(self.texture_count)
        writer.write_uint8(self.has_lightmap)
        writer.write_uint8(self.rotate_texture)
        writer.write_uint8(self.background)
        writer.write_uint8(self.has_shadow)
        writer.write_uint8(self.beaming)
        writer.write_uint8(self.render)
        writer.write_uint8(self.dirt_enabled)  # Dirt/weathering overlay texture enabled
        # Dirt texture name: fixed-size 32-byte char array (null-padded).
        writer.write_string(self.dirt_texture, string_length=32, padding="\0")
        writer.write_uint8(self.unknown9)  # TODO: what is this?
        writer.write_uint8(self.dirt_coordinate_space)  # UV coordinate space for dirt texture overlay
        writer.write_single(self.total_area)
        writer.write_uint32(self.unknown11)  # Reserved field (part of L[3] sequence after total_area) - always 0
        if game == Game.K2:
            writer.write_uint32(self.unknown12)  # Reserved field (K2 only, part of L[3] sequence after total_area) - always 0
            writer.write_uint32(self.unknown13)  # Reserved field (K2 only, part of L[3] sequence after total_area) - always 0
        writer.write_uint32(self.mdx_data_offset)
        writer.write_uint32(self.vertices_offset)

        # Do NOT perform K1 fixed-offset patching here; it can overlap tail flag bytes depending on
        # which K1 layout variant the file uses. Our reader handles K1 variants via conditional recovery.

    def header_size(
        self,
        game: Game,
    ) -> int:
        return _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE

    def faces_size(
        self,
    ) -> int:
        return len(self.faces) * _Face.SIZE

    def vertices_size(
        self,
    ) -> int:
        return len(self.vertices) * 12


class _DanglymeshHeader:
    def __init__(
        self,
    ):
        self.offset_to_contraints: int = 0
        self.constraints_count: int = 0
        self.constraints_count2: int = 0
        self.displacement: float = 0.0
        self.tightness: float = 0.0
        self.period: float = 0.0
        self.unknown0: int = 0  # TODO: what is this?

    def read(
        self,
        reader: BinaryReader,
    ) -> _DanglymeshHeader:
        self.offset_to_contraints = reader.read_uint32()
        self.constraints_count = reader.read_uint32()
        self.constraints_count2 = reader.read_uint32()
        self.displacement = reader.read_single()
        self.tightness = reader.read_single()
        self.period = reader.read_single()
        self.unknown0 = reader.read_uint32()  # TODO: what is this?
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint32(self.offset_to_contraints)
        writer.write_uint32(self.constraints_count)
        writer.write_uint32(self.constraints_count2)
        writer.write_single(self.displacement)
        writer.write_single(self.tightness)
        writer.write_single(self.period)
        writer.write_uint32(self.unknown0)  # TODO: what is this?


class _SkinmeshHeader:
    SIZE: ClassVar[int] = 100

    def __init__(
        self,
    ):
        self.unknown2: int = 0  # TODO: what is this?
        self.unknown3: int = 0  # TODO: what is this?
        self.unknown4: int = 0  # TODO: what is this?
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
        self.unknown0_count: int = 0  # TODO: what is this?
        self.unknown0_count2: int = 0  # TODO: what is this?
        self.bones: tuple[int, ...] = tuple(-1 for _ in range(16))
        self.unknown1: int = 0  # TODO: what is this?

        # NOTE: Some implementations store bonemap values as float32; we store them as ints.
        self.bonemap: list[int] = []
        self.tbones: list[Vector3] = []
        self.qbones: list[Vector4] = []

    def read(
        self,
        reader: BinaryReader,
    ) -> _SkinmeshHeader:
        self.unknown2 = reader.read_int32()  # TODO: what is this?
        self.unknown3 = reader.read_int32()  # TODO: what is this?
        self.unknown4 = reader.read_int32()  # TODO: what is this?
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
        self.offset_to_unknown0 = reader.read_uint32()
        self.unknown0_count = reader.read_uint32()  # TODO: what is this?
        self.unknown0_count2 = reader.read_uint32()  # TODO: what is this?
        self.bones = tuple(reader.read_uint16() for _ in range(16))
        self.unknown1 = reader.read_uint32()  # TODO: what is this?
        return self

    def read_extra(
        self,
        reader: BinaryReader,
    ):
        # All offsets in MDL are relative to the MDL data section. Some models (or partially read headers)
        # may contain invalid offsets; guard against OOB seeks to keep parsing robust.
        if self.offset_to_bonemap not in (0, 0xFFFFFFFF) and self.bonemap_count > 0:
            # bonemap is stored as floats in some implementations; keep current behavior but validate bounds.
            bonemap_bytes = self.bonemap_count * 4
            if self.offset_to_bonemap <= reader.size() and (self.offset_to_bonemap + bonemap_bytes) <= reader.size():
                reader.seek(self.offset_to_bonemap)
                self.bonemap = [int(reader.read_single()) for _ in range(self.bonemap_count)]

        if self.offset_to_tbones not in (0, 0xFFFFFFFF) and self.tbones_count > 0:
            tbones_bytes = self.tbones_count * 12
            if self.offset_to_tbones <= reader.size() and (self.offset_to_tbones + tbones_bytes) <= reader.size():
                reader.seek(self.offset_to_tbones)
                self.tbones = [reader.read_vector3() for _ in range(self.tbones_count)]

        if self.offset_to_qbones not in (0, 0xFFFFFFFF) and self.qbones_count > 0:
            qbones_bytes = self.qbones_count * 16
            if self.offset_to_qbones <= reader.size() and (self.offset_to_qbones + qbones_bytes) <= reader.size():
                reader.seek(self.offset_to_qbones)
                self.qbones = [reader.read_vector4() for _ in range(self.qbones_count)]

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_int32(self.unknown2)  # TODO: what is this?
        writer.write_int32(self.unknown3)  # TODO: what is this?
        writer.write_int32(self.unknown4)  # TODO: what is this?
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
        writer.write_uint32(self.offset_to_unknown0)
        writer.write_uint32(self.unknown0_count)  # TODO: what is this?
        writer.write_uint32(self.unknown0_count2)  # TODO: what is this?
        for i in range(16):
            writer.write_uint16(self.bones[i])
        writer.write_uint32(self.unknown1)  # TODO: what is this?


class _SaberHeader:
    def __init__(
        self,
    ):
        self.offset_to_vertices: int = 0
        self.offset_to_texcoords: int = 0
        self.offset_to_normals: int = 0
        self.unknown0: int = 0  # TODO: what is this?
        self.unknown1: int = 0  # TODO: what is this?

    def read(
        self,
        reader: BinaryReader,
    ) -> _SaberHeader:
        self.offset_to_vertices = reader.read_uint32()
        self.offset_to_texcoords = reader.read_uint32()
        self.offset_to_normals = reader.read_uint32()
        self.unknown0 = reader.read_uint32()  # TODO: what is this?
        self.unknown1 = reader.read_uint32()  # TODO: what is this?
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint32(self.offset_to_vertices)
        writer.write_uint32(self.offset_to_texcoords)
        writer.write_uint32(self.offset_to_normals)
        writer.write_uint32(self.unknown0)  # TODO: what is this?
        writer.write_uint32(self.unknown1)  # TODO: what is this?


class _LightHeader:
    def __init__(
        self,
    ):
        self.offset_to_unknown0: int = 0
        self.unknown0_count: int = 0
        self.unknown0_count2: int = 0
        self.offset_to_flare_sizes: int = 0
        self.flare_sizes_count: int = 0
        self.flare_sizes_count2: int = 0
        self.offset_to_flare_positions: int = 0
        self.flare_positions_count: int = 0
        self.flare_positions_count2: int = 0
        self.offset_to_flare_colors: int = 0
        self.flare_colors_count: int = 0
        self.flare_colors_count2: int = 0
        self.offset_to_flare_textures: int = 0
        self.flare_textures_count: int = 0
        self.flare_textures_count2: int = 0
        self.flare_radius: float = 0.0
        self.light_priority: int = 0
        self.ambient_only: int = 0
        self.dynamic_type: int = 0
        self.affect_dynamic: int = 0
        self.shadow: int = 0
        self.flare: int = 0
        self.fading_light: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _LightHeader:
        self.offset_to_unknown0 = reader.read_uint32()
        self.unknown0_count = reader.read_uint32()  # TODO: what is this?
        self.unknown0_count2 = reader.read_uint32()  # TODO: what is this?
        self.offset_to_flare_sizes = reader.read_uint32()
        self.flare_sizes_count = reader.read_uint32()
        self.flare_sizes_count2 = reader.read_uint32()
        self.offset_to_flare_positions = reader.read_uint32()
        self.flare_positions_count = reader.read_uint32()
        self.flare_positions_count2 = reader.read_uint32()
        self.offset_to_flare_colors = reader.read_uint32()
        self.flare_colors_count = reader.read_uint32()
        self.flare_colors_count2 = reader.read_uint32()
        self.offset_to_flare_textures = reader.read_uint32()
        self.flare_textures_count = reader.read_uint32()
        self.flare_textures_count2 = reader.read_uint32()
        self.flare_radius = reader.read_single()
        self.light_priority = reader.read_uint32()
        self.ambient_only = reader.read_uint32()
        self.dynamic_type = reader.read_uint32()
        self.affect_dynamic = reader.read_uint32()
        self.shadow = reader.read_uint32()
        self.flare = reader.read_uint32()
        self.fading_light = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint32(self.offset_to_unknown0)  # TODO: what is this?
        writer.write_uint32(self.unknown0_count)  # TODO: what is this?
        writer.write_uint32(self.unknown0_count2)  # TODO: what is this?
        writer.write_uint32(self.offset_to_flare_sizes)
        writer.write_uint32(self.flare_sizes_count)
        writer.write_uint32(self.flare_sizes_count2)
        writer.write_uint32(self.offset_to_flare_positions)
        writer.write_uint32(self.flare_positions_count)
        writer.write_uint32(self.flare_positions_count2)
        writer.write_uint32(self.offset_to_flare_colors)
        writer.write_uint32(self.flare_colors_count)
        writer.write_uint32(self.flare_colors_count2)
        writer.write_uint32(self.offset_to_flare_textures)
        writer.write_uint32(self.flare_textures_count)
        writer.write_uint32(self.flare_textures_count2)
        writer.write_single(self.flare_radius)
        writer.write_uint32(self.light_priority)
        writer.write_uint32(self.ambient_only)
        writer.write_uint32(self.dynamic_type)
        writer.write_uint32(self.affect_dynamic)
        writer.write_uint32(self.shadow)
        writer.write_uint32(self.flare)
        writer.write_uint32(self.fading_light)


class _EmitterHeader:
    def __init__(
        self,
    ):
        self.dead_space: float = 0.0
        self.blast_radius: float = 0.0
        self.blast_length: float = 0.0
        self.branch_count: int = 0
        self.smoothing: float = 0.0
        self.grid: Vector2 = Vector2.from_null()
        self.update: str = ""
        self.render: str = ""
        self.blend: str = ""
        self.texture: str = ""
        self.chunk_name: str = ""
        self.twosided_texture: int = 0
        self.loop: int = 0
        self.render_order: int = 0
        self.frame_blending: int = 0
        self.depth_texture: str = ""
        self.unknown0: int = 0
        self.flags: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _EmitterHeader:
        self.dead_space = reader.read_single()
        self.blast_radius = reader.read_single()
        self.blast_length = reader.read_single()
        self.branch_count = reader.read_uint32()
        self.smoothing = reader.read_single()
        self.grid = reader.read_vector2()
        self.update = reader.read_terminated_string("\0", 32)
        self.render = reader.read_terminated_string("\0", 32)
        self.blend = reader.read_terminated_string("\0", 32)
        self.texture = reader.read_terminated_string("\0", 32)
        self.chunk_name = reader.read_terminated_string("\0", 32)
        self.twosided_texture = reader.read_uint32()
        self.loop = reader.read_uint32()
        self.render_order = reader.read_uint32()
        self.frame_blending = reader.read_uint32()
        self.depth_texture = reader.read_terminated_string("\0", 32)
        self.unknown0 = reader.read_uint8()
        self.flags = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_single(self.dead_space)
        writer.write_single(self.blast_radius)
        writer.write_single(self.blast_length)
        writer.write_uint32(self.branch_count)
        writer.write_single(self.smoothing)
        writer.write_vector2(self.grid)
        writer.write_string(self.update, string_length=32, encoding="ascii")
        writer.write_string(self.render, string_length=32, encoding="ascii")
        writer.write_string(self.blend, string_length=32, encoding="ascii")
        writer.write_string(self.texture, string_length=32, encoding="ascii")
        writer.write_string(self.chunk_name, string_length=32, encoding="ascii")
        writer.write_uint32(self.twosided_texture)
        writer.write_uint32(self.loop)
        writer.write_uint32(self.render_order)
        writer.write_uint32(self.frame_blending)
        writer.write_string(self.depth_texture, string_length=32, encoding="ascii")
        writer.write_uint8(self.unknown0)
        writer.write_uint32(self.flags)


class _ReferenceHeader:
    def __init__(
        self,
    ):
        self.model: str = ""
        self.reattachable: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _ReferenceHeader:
        self.model = reader.read_terminated_string("\0", 32)
        self.reattachable = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_string(self.model, string_length=32, encoding="ascii")
        writer.write_uint32(self.reattachable)


class _Face:
    SIZE = 32

    def __init__(
        self,
    ):
        self.normal: Vector3 = Vector3.from_null()
        self.plane_coefficient: float = 0.0
        self.material: int = 0
        self.adjacent1: int = 0
        self.adjacent2: int = 0
        self.adjacent3: int = 0
        self.vertex1: int = 0
        self.vertex2: int = 0
        self.vertex3: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _Face:
        self.normal = reader.read_vector3()
        self.plane_coefficient = reader.read_single()
        self.material = reader.read_uint32()
        self.adjacent1 = reader.read_uint16()
        self.adjacent2 = reader.read_uint16()
        self.adjacent3 = reader.read_uint16()
        self.vertex1 = reader.read_uint16()
        self.vertex2 = reader.read_uint16()
        self.vertex3 = reader.read_uint16()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_vector3(self.normal)
        writer.write_single(self.plane_coefficient)
        writer.write_uint32(self.material)
        writer.write_uint16(self.adjacent1)
        writer.write_uint16(self.adjacent2)
        writer.write_uint16(self.adjacent3)
        writer.write_uint16(self.vertex1)
        writer.write_uint16(self.vertex2)
        writer.write_uint16(self.vertex3)


# Geometry calculation utilities
# Reference: vendor/mdlops/MDLOpsM.pm:463-520


def _calculate_face_area(v1: Vector3, v2: Vector3, v3: Vector3) -> float:
    """Calculate a triangle face's surface area using Heron's formula.

    Args:
    ----
        v1: First vertex position
        v2: Second vertex position
        v3: Third vertex position

    Returns:
    -------
        The surface area of the triangle

    References:
    ----------
        vendor/mdlops/MDLOpsM.pm:465-488 - facearea() function
        Formula: Uses Heron's formula with semi-perimeter
    """
    # Calculate edge lengths (mdlops:471-482)
    import math

    a = math.sqrt((v1.x - v2.x) ** 2 + (v1.y - v2.y) ** 2 + (v1.z - v2.z) ** 2)

    b = math.sqrt((v1.x - v3.x) ** 2 + (v1.y - v3.y) ** 2 + (v1.z - v3.z) ** 2)

    c = math.sqrt((v2.x - v3.x) ** 2 + (v2.y - v3.y) ** 2 + (v2.z - v3.z) ** 2)

    # Semi-perimeter (mdlops:483)
    s = (a + b + c) / 2.0

    # Heron's formula (mdlops:485-487)
    inter = s * (s - a) * (s - b) * (s - c)
    return math.sqrt(inter) if inter > 0.0 else 0.0


def _decompress_quaternion(compressed: int) -> Vector4:
    """Decompress a packed quaternion from a 32-bit integer.

    KotOR uses compressed quaternions for orientation controllers to save space.
    The compression packs X, Y, Z components into 11, 11, and 10 bits respectively,
    with W calculated from the constraint that |q| = 1.

    Args:
    ----
        compressed: 32-bit packed quaternion value

    Returns:
    -------
        Vector4: Decompressed quaternion (x, y, z, w)

    References:
    ----------
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:850-868
        Formula: X uses bits 0-10 (11 bits), Y uses bits 11-21 (11 bits),
                 Z uses bits 22-31 (10 bits), W computed from magnitude

    Notes:
    -----
        The compressed format maps values to [-1, 1] range:
        - X: 11 bits -> [0, 2047] -> mapped to [-1, 1]
        - Y: 11 bits -> [0, 2047] -> mapped to [-1, 1]
        - Z: 10 bits -> [0, 1023] -> mapped to [-1, 1]
        - W: Computed from sqrt(1 - x² - y² - z²) if mag < 1, else 0
    """
    # Extract components from packed integer (kotorblender:855-858)
    # X component: bits 0-10 (11 bits, mask 0x7FF = 2047)
    x = ((compressed & 0x7FF) / 1023.0) - 1.0

    # Y component: bits 11-21 (11 bits, shift 11 then mask 0x7FF)
    y = (((compressed >> 11) & 0x7FF) / 1023.0) - 1.0

    # Z component: bits 22-31 (10 bits, shift 22, max value 1023)
    z = ((compressed >> 22) / 511.0) - 1.0

    # Calculate W from quaternion unit constraint (kotorblender:859-863)
    mag2 = x * x + y * y + z * z
    if mag2 < 1.0:
        import math

        w = math.sqrt(1.0 - mag2)
    else:
        w = 0.0

    return Vector4(x, y, z, w)


def _compress_quaternion(quat: Vector4) -> int:
    """Compress a quaternion into a 32-bit integer.

    Inverse of _decompress_quaternion. Packs X, Y, Z components into a single
    32-bit value. The W component is not stored as it can be recomputed from
    the quaternion unit constraint.

    Args:
    ----
        quat: Quaternion to compress (x, y, z, w)

    Returns:
    -------
        int: 32-bit packed quaternion value

    References:
    ----------
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:850-868 (decompression)
        Inverse operation derived from decompression algorithm

    Notes:
    -----
        Values are clamped to [-1, 1] range before packing to prevent overflow.
    """

    # Clamp values to valid range
    x = max(-1.0, min(1.0, quat.x))
    y = max(-1.0, min(1.0, quat.y))
    z = max(-1.0, min(1.0, quat.z))

    # Map from [-1, 1] to integer ranges and pack
    # X: [-1, 1] -> [0, 2047] (11 bits)
    x_packed = int((x + 1.0) * 1023.0) & 0x7FF

    # Y: [-1, 1] -> [0, 2047] (11 bits)
    y_packed = int((y + 1.0) * 1023.0) & 0x7FF

    # Z: [-1, 1] -> [0, 1023] (10 bits)
    z_packed = int((z + 1.0) * 511.0) & 0x3FF

    # Pack into single 32-bit integer
    return x_packed | (y_packed << 11) | (z_packed << 22)


def _calculate_face_normal(
    v1: Vector3,
    v2: Vector3,
    v3: Vector3,
) -> tuple[Vector3, float]:
    """Calculate a triangle face normal and triangle area.

    Returns:
        (normal, area) where:
        - normal is a unit-length Vector3 (or zero-vector if degenerate)
        - area is the triangle area (always non-negative)
    """
    # Edges
    e1 = Vector3(v2.x - v1.x, v2.y - v1.y, v2.z - v1.z)
    e2 = Vector3(v3.x - v1.x, v3.y - v1.y, v3.z - v1.z)

    # Cross product e1 x e2
    cx = (e1.y * e2.z) - (e1.z * e2.y)
    cy = (e1.z * e2.x) - (e1.x * e2.z)
    cz = (e1.x * e2.y) - (e1.y * e2.x)

    mag = math.sqrt((cx * cx) + (cy * cy) + (cz * cz))
    area = 0.5 * mag
    if mag <= 0.0:
        return Vector3.from_null(), 0.0

    inv = 1.0 / mag
    return Vector3(cx * inv, cy * inv, cz * inv), area


def _calculate_tangent_space(
    v0: Vector3,
    v1: Vector3,
    v2: Vector3,
    uv0: tuple[float, float],
    uv1: tuple[float, float],
    uv2: tuple[float, float],
    face_normal: Vector3,
) -> tuple[Vector3, Vector3]:
    """Calculate tangent and binormal vectors for a triangle face.

    Uses the standard UV-derivative method and returns normalized vectors. For degenerate
    UVs, returns a stable fallback basis.
    """
    # Position deltas
    dp1 = Vector3(v1.x - v0.x, v1.y - v0.y, v1.z - v0.z)
    dp2 = Vector3(v2.x - v0.x, v2.y - v0.y, v2.z - v0.z)

    # UV deltas
    duv1x, duv1y = (uv1[0] - uv0[0]), (uv1[1] - uv0[1])
    duv2x, duv2y = (uv2[0] - uv0[0]), (uv2[1] - uv0[1])

    det = (duv1x * duv2y) - (duv1y * duv2x)
    if abs(det) < 1e-12:
        return Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)

    r = 1.0 / det
    tx = (dp1.x * duv2y - dp2.x * duv1y) * r
    ty = (dp1.y * duv2y - dp2.y * duv1y) * r
    tz = (dp1.z * duv2y - dp2.z * duv1y) * r
    bx = (dp2.x * duv1x - dp1.x * duv2x) * r
    by = (dp2.y * duv1x - dp1.y * duv2x) * r
    bz = (dp2.z * duv1x - dp1.z * duv2x) * r

    # Orthonormalize tangent against normal
    dot_nt = (face_normal.x * tx) + (face_normal.y * ty) + (face_normal.z * tz)
    tx -= face_normal.x * dot_nt
    ty -= face_normal.y * dot_nt
    tz -= face_normal.z * dot_nt

    tlen = math.sqrt((tx * tx) + (ty * ty) + (tz * tz))
    if tlen <= 1e-12:
        tangent = Vector3(1.0, 0.0, 0.0)
    else:
        inv = 1.0 / tlen
        tangent = Vector3(tx * inv, ty * inv, tz * inv)

    # Orthonormalize binormal against normal and tangent
    dot_nb = (face_normal.x * bx) + (face_normal.y * by) + (face_normal.z * bz)
    bx -= face_normal.x * dot_nb
    by -= face_normal.y * dot_nb
    bz -= face_normal.z * dot_nb
    dot_tb = (tangent.x * bx) + (tangent.y * by) + (tangent.z * bz)
    bx -= tangent.x * dot_tb
    by -= tangent.y * dot_tb
    bz -= tangent.z * dot_tb

    blen = math.sqrt((bx * bx) + (by * by) + (bz * bz))
    if blen <= 1e-12:
        binormal = Vector3(0.0, 1.0, 0.0)
    else:
        inv = 1.0 / blen
        binormal = Vector3(bx * inv, by * inv, bz * inv)

    return tangent, binormal


class MDLBinaryReader:
    """Binary MDL/MDX file reader.

    This class provides loading of MDL (model) and MDX (model extension) files.
    Supports both full loading and fast loading optimized for rendering.

    Args:
    ----
        source: The source of the MDL data
        offset: The byte offset within the source
        size: Size of the data to read
        source_ext: The source of the MDX data
        offset_ext: The byte offset within the MDX source
        size_ext: Size of the MDX data to read
        game: The game version (K1 or K2)
        fast_load: If True, skips animations and controllers for faster loading (optimized for rendering)

    References:
    ----------
        vendor/mdlops/MDLOpsM.pm:1649-1778 (Controller structure and bezier detection)
        vendor/mdlops/MDLOpsM.pm:5470-5596 (Tangent space calculation)
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:187-721 (Controller reading)
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723 (Skin bone preparation)
        vendor/kotorblender/format/mdl/reader.py:850-868 (Quaternion decompression)
        vendor/KotOR.js/src/loaders/MDLLoader.ts (Model loading architecture)
    """

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
        source_ext: SOURCE_TYPES | None = None,
        offset_ext: int = 0,
        size_ext: int = 0,
        game: Game = Game.K2,
        fast_load: bool = False,
    ):
        self._reader: BinaryReader = BinaryReader.from_auto(source, offset)

        self._reader_ext: BinaryReader | None = None if source_ext is None else BinaryReader.from_auto(source_ext, offset_ext)

        # first 12 bytes do not count in offsets used within the file
        self._reader.set_offset(self._reader.offset() + 12)

        self._fast_load: bool = fast_load
        self.game: Game = game

    def load(
        self,
        auto_close: bool = True,  # noqa: FBT002, FBT001
    ) -> MDL:
        """Load the MDL file.

        Args:
        ----
            auto_close: If True, automatically close readers after loading

        Returns:
        -------
            The loaded MDL instance
        """
        self._mdl: MDL = MDL()
        self._names: list[str] = []

        model_header: _ModelHeader = _ModelHeader().read(self._reader)

        # Determine game version from the file header function pointers.
        # This is more reliable than using per-node function pointer values.
        if model_header.geometry.function_pointer0 == _GeometryHeader.K1_FUNCTION_POINTER0 and model_header.geometry.function_pointer1 == _GeometryHeader.K1_FUNCTION_POINTER1:
            self.game = Game.K1
        elif (
            model_header.geometry.function_pointer0 == _GeometryHeader.K2_FUNCTION_POINTER0 and model_header.geometry.function_pointer1 == _GeometryHeader.K2_FUNCTION_POINTER1
        ):
            self.game = Game.K2

        self._mdl.name = model_header.geometry.model_name
        self._mdl.supermodel = model_header.supermodel
        self._mdl.fog = bool(model_header.fog)
        # model_type corresponds to classification
        self._mdl.classification = MDLClassification(model_header.model_type)
        # unknown0 corresponds to classification_unk1
        self._mdl.classification_unk1 = model_header.unknown0
        self._mdl.animation_scale = model_header.anim_scale

        self._load_names(model_header)
        self._mdl.root = self._load_node(model_header.geometry.root_node_offset)

        # Skip animations when fast loading (not needed for rendering)
        if not self._fast_load:
            self._reader.seek(model_header.offset_to_animations)
            animation_offsets: list[int] = [self._reader.read_uint32() for _ in range(model_header.animation_count)]
            for animation_offset in animation_offsets:
                anim: MDLAnimation = self._load_anim(animation_offset)
                self._mdl.anims.append(anim)

        if auto_close:
            self._reader.close()
            if self._reader_ext is not None:
                self._reader_ext.close()

        return self._mdl

    def _load_names(
        self,
        model_header: _ModelHeader,
    ):
        self._reader.seek(model_header.offset_to_name_offsets)
        name_offsets: list[int] = [self._reader.read_uint32() for _ in range(model_header.name_offsets_count)]
        for offset in name_offsets:
            self._reader.seek(offset)
            name = self._reader.read_terminated_string("\0")
            self._names.append(name)

    def _load_node(
        self,
        offset: int,
    ) -> MDLNode:
        self._reader.seek(offset)
        bin_node = _Node().read(self._reader, self.game)
        assert bin_node.header is not None

        node = MDLNode()
        node.node_id = bin_node.header.node_id
        node.name = self._names[bin_node.header.name_id]
        node.position = bin_node.header.position
        node.orientation = bin_node.header.orientation
        node.node_type = MDLNodeType.DUMMY

        # Check for AABB flag - nodes with AABB flag should be marked as AABB type
        # A node can have both MESH and AABB flags (walkmesh with visible geometry)
        if bin_node.header.type_id & MDLNodeFlags.AABB:
            node.node_type = MDLNodeType.AABB
            # TODO: Read AABB/walkmesh data from binary when AABB flag is set
            # For now, create empty walkmesh to preserve the AABB node type
            from pykotor.resource.formats.mdl.mdl_data import MDLWalkmesh

            if node.aabb is None:
                node.aabb = MDLWalkmesh()

        # Check for LIGHT flag - nodes with LIGHT flag should be marked as LIGHT type
        if bin_node.header.type_id & MDLNodeFlags.LIGHT:
            node.node_type = MDLNodeType.LIGHT
            from pykotor.resource.formats.mdl.mdl_data import MDLLight, MDLDynamicType

            if bin_node.light is not None:
                node.light = MDLLight()
                node.light.ambient_only = bool(bin_node.light.ambient_only)
                node.light.dynamic_type = MDLDynamicType(bin_node.light.dynamic_type)
                node.light.shadow = bool(bin_node.light.shadow)
                node.light.flare = bool(bin_node.light.flare)
                node.light.light_priority = bin_node.light.light_priority
                node.light.fading_light = bool(bin_node.light.fading_light)
                node.light.flare_radius = bin_node.light.flare_radius
                
                # Read flare data (sizes, positions, colors, textures)
                # Reference: vendor/MDLOps/MDLOpsM.pm:1875-1954 (flare data reading)
                light_header = bin_node.light
                
                # Flare textures: array of string pointers, each pointing to a 12-byte null-terminated string
                if light_header.flare_textures_count > 0 and light_header.offset_to_flare_textures not in (0, 0xFFFFFFFF):
                    node.light.flare_textures = []
                    saved_pos = self._reader.position()
                    try:
                        # Read texture name pointers (each pointer is 4 bytes)
                        self._reader.seek(light_header.offset_to_flare_textures)
                        texture_pointers: list[int] = []
                        for _ in range(light_header.flare_textures_count):
                            if self._reader.position() + 4 <= self._reader.size():
                                ptr = self._reader.read_uint32()
                                if ptr not in (0, 0xFFFFFFFF):
                                    texture_pointers.append(ptr)
                        
                        # Read texture names from pointers
                        for texture_ptr in texture_pointers:
                            if texture_ptr <= self._reader.size() - 12:
                                self._reader.seek(texture_ptr)
                                texture_name = self._reader.read_terminated_string("\0", 12)
                                if texture_name:
                                    node.light.flare_textures.append(texture_name)
                    finally:
                        self._reader.seek(saved_pos)
                
                # Flare sizes: array of floats (4 bytes each)
                if light_header.flare_sizes_count > 0 and light_header.offset_to_flare_sizes not in (0, 0xFFFFFFFF):
                    node.light.flare_sizes = []
                    saved_pos = self._reader.position()
                    try:
                        self._reader.seek(light_header.offset_to_flare_sizes)
                        for _ in range(light_header.flare_sizes_count):
                            if self._reader.position() + 4 <= self._reader.size():
                                size = self._reader.read_single()
                                node.light.flare_sizes.append(size)
                    finally:
                        self._reader.seek(saved_pos)
                
                # Flare positions: array of floats (4 bytes each)
                if light_header.flare_positions_count > 0 and light_header.offset_to_flare_positions not in (0, 0xFFFFFFFF):
                    node.light.flare_positions = []
                    saved_pos = self._reader.position()
                    try:
                        self._reader.seek(light_header.offset_to_flare_positions)
                        for _ in range(light_header.flare_positions_count):
                            if self._reader.position() + 4 <= self._reader.size():
                                position = self._reader.read_single()
                                node.light.flare_positions.append(position)
                    finally:
                        self._reader.seek(saved_pos)
                
                # Flare color shifts: array of Vector3 (12 bytes each = 3 floats)
                if light_header.flare_colors_count > 0 and light_header.offset_to_flare_colors not in (0, 0xFFFFFFFF):
                    node.light.flare_color_shifts = []
                    saved_pos = self._reader.position()
                    try:
                        self._reader.seek(light_header.offset_to_flare_colors)
                        for _ in range(light_header.flare_colors_count):
                            if self._reader.position() + 12 <= self._reader.size():
                                r = self._reader.read_single()
                                g = self._reader.read_single()
                                b = self._reader.read_single()
                                node.light.flare_color_shifts.append((r, g, b))
                    finally:
                        self._reader.seek(saved_pos)

        # Check for EMITTER flag - nodes with EMITTER flag should be marked as EMITTER type
        if bin_node.header.type_id & MDLNodeFlags.EMITTER:
            node.node_type = MDLNodeType.EMITTER
            from pykotor.resource.formats.mdl.mdl_data import MDLEmitter

            if bin_node.emitter is not None:
                node.emitter = MDLEmitter()
                node.emitter.dead_space = bin_node.emitter.dead_space
                node.emitter.blast_radius = bin_node.emitter.blast_radius
                node.emitter.blast_length = bin_node.emitter.blast_length
                node.emitter.branch_count = bin_node.emitter.branch_count
                node.emitter.control_point_smoothing = bin_node.emitter.smoothing
                node.emitter.x_grid = int(bin_node.emitter.grid.x)
                node.emitter.y_grid = int(bin_node.emitter.grid.y)
                node.emitter.update = bin_node.emitter.update
                node.emitter.render = bin_node.emitter.render
                node.emitter.blend = bin_node.emitter.blend
                node.emitter.texture = bin_node.emitter.texture
                node.emitter.chunk_name = bin_node.emitter.chunk_name
                node.emitter.two_sided_texture = bin_node.emitter.twosided_texture
                node.emitter.loop = bin_node.emitter.loop
                node.emitter.render_order = bin_node.emitter.render_order
                node.emitter.frame_blender = bin_node.emitter.frame_blending
                node.emitter.depth_texture = bin_node.emitter.depth_texture
                node.emitter.flags = bin_node.emitter.flags
                # TODO: Read additional emitter data if needed

        # Check for REFERENCE flag - nodes with REFERENCE flag should be marked as REFERENCE type
        if bin_node.header.type_id & MDLNodeFlags.REFERENCE:
            node.node_type = MDLNodeType.REFERENCE
            from pykotor.resource.formats.mdl.mdl_data import MDLReference

            if bin_node.reference is not None:
                node.reference = MDLReference()
                node.reference.model = bin_node.reference.model
                node.reference.reattachable = bool(bin_node.reference.reattachable)

        if bin_node.trimesh is not None:
            node.mesh = MDLMesh()
            # Only set TRIMESH type if special node type flags are not set
            # A node can have both MESH and AABB flags (walkmesh with visible geometry)
            # LIGHT, EMITTER, and REFERENCE flags also take precedence over TRIMESH
            if not (bin_node.header.type_id & (MDLNodeFlags.AABB | MDLNodeFlags.LIGHT | MDLNodeFlags.EMITTER | MDLNodeFlags.REFERENCE)):
                node.node_type = MDLNodeType.TRIMESH
            node.mesh.shadow = bool(bin_node.trimesh.has_shadow)
            # render is stored as uint8 in binary (0 or 1), convert to bool for MDLMesh
            # bool(0) = False, bool(1) = True, bool(any non-zero) = True
            node.mesh.render = bool(bin_node.trimesh.render)
            node.mesh.background_geometry = bool(bin_node.trimesh.background)
            node.mesh.has_lightmap = bool(bin_node.trimesh.has_lightmap)
            node.mesh.beaming = bool(bin_node.trimesh.beaming)
            node.mesh.dirt_enabled = bool(bin_node.trimesh.dirt_enabled)
            node.mesh.dirt_texture = bin_node.trimesh.dirt_texture
            node.mesh.dirt_coordinate_space = bin_node.trimesh.dirt_coordinate_space
            node.mesh.diffuse = Color.from_bgr_vector3(bin_node.trimesh.diffuse)
            node.mesh.ambient = Color.from_bgr_vector3(bin_node.trimesh.ambient)
            node.mesh.texture_1 = bin_node.trimesh.texture1
            node.mesh.texture_2 = bin_node.trimesh.texture2
            node.mesh.bb_min = bin_node.trimesh.bounding_box_min
            node.mesh.bb_max = bin_node.trimesh.bounding_box_max
            node.mesh.radius = bin_node.trimesh.radius
            node.mesh.average = bin_node.trimesh.average
            node.mesh.area = bin_node.trimesh.total_area
            node.mesh.transparency_hint = bin_node.trimesh.transparency_hint
            # Stored as 8 raw bytes in the binary trimesh header; normalize to a tuple[int,...] for MDLMesh.
            node.mesh.saber_unknowns = cast(
                "tuple[int, int, int, int, int, int, int, int]",
                tuple(int(b) for b in bin_node.trimesh.saber_unknowns),
            )

            # Vertex positions can be stored either in MDL (K1-style) or in MDX blocks.
            # Verify vertex_count by checking actual data availability, not by inference.
            vcount = bin_node.trimesh.vertex_count
            vcount_verified: bool = False

            # Verify vertex_count by checking actual data in the file
            # If vertex_count is suspiciously low (0 or 1), try to determine the correct count from actual data
            # Also check faces - they reference vertex indices, so vertex_count must be at least max_vertex_index + 1
            # But we need to validate that we can actually read that many vertices from the file
            # Always check faces if vcount is suspiciously low, even if there are no faces (vcount of 0 or 1 is almost always wrong)
            # First, check faces to determine minimum required vertex_count (faces are authoritative)
            required_vertex_count = 0
            if bin_node.trimesh.faces_count > 0:
                max_vertex_index = 0
                for face in bin_node.trimesh.faces:
                    max_vertex_index = max(max_vertex_index, face.vertex1, face.vertex2, face.vertex3)
                required_vertex_count = max_vertex_index + 1
            
            # CRITICAL: If vcount is suspiciously low (0 or 1), ALWAYS try to recover from faces or file bounds
            # Even if faces don't exist yet, vcount of 0 or 1 is almost always wrong for meshes with geometry
            # If faces exist and require more vertices, that's the authoritative count
            if vcount <= 1 or required_vertex_count > vcount:
                
                # If we have a required count from faces, or if vcount is 0/1 (suspicious), try to validate/read from file
                # When there are no faces, we should still try to determine vertex count from file bounds
                # Always run validation if vcount is suspiciously low (0 or 1) OR if faces require more vertices
                if vcount <= 1 or required_vertex_count > vcount:
                    # Validate that we can actually read this many vertices from the file
                    # Start with the required count, then limit if bounds check fails
                    can_read_count = required_vertex_count if required_vertex_count > 0 else 0
                    if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX) and self._reader_ext:
                        # Check MDX bounds
                        mdx_vertex_data_offset: int = bin_node.trimesh.mdx_data_offset
                        mdx_vertex_data_block_size: int = bin_node.trimesh.mdx_data_size
                        vertex_offset = bin_node.trimesh.mdx_vertex_offset
                        if mdx_vertex_data_offset not in (0, 0xFFFFFFFF) and mdx_vertex_data_block_size > 0:
                            # If no faces, try to determine count from available MDX data
                            if bin_node.trimesh.faces_count == 0:
                                # Calculate max vertices that can fit in MDX
                                available_bytes = self._reader_ext.size() - mdx_vertex_data_offset - vertex_offset
                                if available_bytes > 0:
                                    can_read_count = available_bytes // mdx_vertex_data_block_size
                                    if can_read_count < 0:
                                        can_read_count = 0
                            else:
                                # Calculate max vertices that can fit in MDX for required count
                                # Always calculate the actual count we can read, even if bounds check passes
                                # For vertex i, position is: mdx_vertex_data_offset + i * mdx_vertex_data_block_size + vertex_offset
                                # For the last vertex (index vcount-1), we need: mdx_vertex_data_offset + (vcount-1) * mdx_vertex_data_block_size + vertex_offset + 12 <= size
                                # Solving: (vcount-1) * mdx_vertex_data_block_size <= size - mdx_vertex_data_offset - vertex_offset - 12
                                # vcount <= (size - mdx_vertex_data_offset - vertex_offset - 12) / mdx_vertex_data_block_size + 1
                                available_for_vertices = self._reader_ext.size() - mdx_vertex_data_offset - vertex_offset - 12
                                if available_for_vertices > 0:
                                    max_vertices_from_mdx = (available_for_vertices // mdx_vertex_data_block_size) + 1
                                    if max_vertices_from_mdx < 0:
                                        max_vertices_from_mdx = 0
                                    # Use the minimum of required count and what we can actually read
                                    can_read_count = min(required_vertex_count, max_vertices_from_mdx) if required_vertex_count > 0 else max_vertices_from_mdx
                                else:
                                    can_read_count = 0
                    elif bin_node.trimesh.vertices_offset not in (0, 0xFFFFFFFF):
                        # Check MDL bounds
                        available_bytes = self._reader.size() - bin_node.trimesh.vertices_offset
                        if available_bytes > 0:
                            max_vertices_from_mdl = available_bytes // 12
                            if max_vertices_from_mdl < 0:
                                max_vertices_from_mdl = 0
                            if bin_node.trimesh.faces_count == 0:
                                # If no faces, use what we can read from MDL
                                can_read_count = max_vertices_from_mdl
                            else:
                                # Use the minimum of required count and what we can actually read
                                can_read_count = min(required_vertex_count, max_vertices_from_mdl) if required_vertex_count > 0 else max_vertices_from_mdl
                        else:
                            can_read_count = 0
                    
                    # Use the validated count (at least what faces require, but not more than we can read)
                    # Also use it if vcount is 0/1 and we found a reasonable count from file bounds
                    # If faces require more vertices than header says, use face-based count but cap to what we can read
                    # (faces are authoritative - if they reference vertex indices, those vertices should exist)
                    # Always prioritize face-based count if faces exist
                    if required_vertex_count > 0:
                        # Faces exist - use face-based count, but cap to what we can actually read
                        # This prevents stream boundary errors while still prioritizing face-based count
                        # If can_read_count is 0, we still need to use required_vertex_count (faces are authoritative)
                        # But we'll verify we can actually read that many vertices later
                        if can_read_count > 0:
                            final_count = min(required_vertex_count, can_read_count)
                        else:
                            # can_read_count is 0, but faces require vertices - use required_vertex_count
                            # We'll verify we can actually read that many vertices in the second recovery pass
                            final_count = required_vertex_count
                        # CRITICAL: Always update vcount if faces require more vertices OR if vcount is suspiciously low (0 or 1)
                        # This ensures we fix vcount even when it's 1 (which is almost always wrong for meshes with geometry)
                        # Even if final_count equals vcount, if vcount is 1 and faces require vertices, we need to verify
                        if final_count > vcount or (vcount <= 1 and final_count > 0):
                            vcount = final_count
                            bin_node.trimesh.vertex_count = final_count
                            vcount_verified = True
                    elif can_read_count > 0 and (can_read_count > vcount or vcount <= 1):
                        # No faces, but we found a count from file bounds (even if it's 1, use it if vcount is 0 or 1)
                        # This ensures we don't leave vcount at 0 or 1 when vertices exist in the file
                        # But never use a count of 1 if we can find a better count
                        if can_read_count > 1 or vcount == 0:
                            vcount = can_read_count
                            bin_node.trimesh.vertex_count = can_read_count
                            vcount_verified = True
            
            # If still suspiciously low, try to count actual vertices from file data
            # Use face-based count as minimum if faces exist (faces are authoritative)
            # Recalculate required count from faces if not already calculated
            if required_vertex_count == 0 and bin_node.trimesh.faces_count > 0:
                max_vertex_index = 0
                for face in bin_node.trimesh.faces:
                    max_vertex_index = max(max_vertex_index, face.vertex1, face.vertex2, face.vertex3)
                required_vertex_count = max_vertex_index + 1
            
            # CRITICAL: If vcount is still suspiciously low OR faces require more vertices, try to count actual vertices
            # Even if vcount_verified was set in the first pass, we need to verify we can actually read the vertices
            # This second pass actually reads vertices to count them, which is more reliable than bounds checking
            if vcount <= 1 or required_vertex_count > vcount:
                if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX) and self._reader_ext:
                    # Vertices are in MDX: try to count actual vertices by reading them
                    mdx_vertex_data_offset = bin_node.trimesh.mdx_data_offset
                    mdx_vertex_data_block_size = bin_node.trimesh.mdx_data_size
                    vertex_offset = bin_node.trimesh.mdx_vertex_offset
                    if mdx_vertex_data_offset not in (0, 0xFFFFFFFF) and mdx_vertex_data_block_size > 0:
                        # Try to read vertices and count them
                        saved_pos = self._reader_ext.position()
                        try:
                            actual_vertex_count = 0
                            # Try reading up to a reasonable limit, but at least what faces require
                            max_to_read = max(required_vertex_count, 100000) if required_vertex_count > 0 else 100000
                            for i in range(max_to_read):
                                seek_pos = mdx_vertex_data_offset + i * mdx_vertex_data_block_size + vertex_offset
                                if seek_pos + 12 > self._reader_ext.size():
                                    break
                                try:
                                    self._reader_ext.seek(seek_pos)
                                    x = self._reader_ext.read_single()
                                    y = self._reader_ext.read_single()
                                    z = self._reader_ext.read_single()
                                    # Basic sanity check: reasonable float values
                                    if (
                                        all(-1e6 <= coord <= 1e6 for coord in (x, y, z))
                                        and all(not (coord != coord) for coord in (x, y, z))  # Not NaN
                                    ):
                                        actual_vertex_count = i + 1
                                    else:
                                        # Hit invalid data, but if we've read enough for faces, use that
                                        if required_vertex_count > 0 and actual_vertex_count >= required_vertex_count:
                                            actual_vertex_count = required_vertex_count
                                        break
                                except Exception:
                                    # Can't read more, but if we've read enough for faces, use that
                                    if required_vertex_count > 0 and actual_vertex_count >= required_vertex_count:
                                        actual_vertex_count = required_vertex_count
                                    break
                            
                            # Only use face-based count if we actually read at least that many vertices
                            # If we didn't read enough, we have a problem - faces reference vertices that don't exist
                            # In that case, we need to verify we can actually read that many vertices before using the face-based count
                            if required_vertex_count > 0:
                                if actual_vertex_count >= required_vertex_count:
                                    # We read enough for faces - use the actual count (may be more than required)
                                    pass  # actual_vertex_count is already correct
                                else:
                                    # We didn't read enough for faces - verify we can actually read that many
                                    # Check if we can read at least required_vertex_count vertices
                                    can_read_required = True
                                    for i in range(actual_vertex_count, required_vertex_count):
                                        seek_pos = mdx_vertex_data_offset + i * mdx_vertex_data_block_size + vertex_offset
                                        if seek_pos + 12 > self._reader_ext.size():
                                            can_read_required = False
                                            break
                                    if can_read_required:
                                        # We can read the required count - use it
                                        actual_vertex_count = required_vertex_count
                                    else:
                                        # We can't read the required count - use what we actually read
                                        # This indicates a problem, but we'll use what we have
                                        pass  # actual_vertex_count stays as what we read
                            
                            # If we found vertices, use the count
                            # CRITICAL: Always update if actual count is greater OR if vcount is suspiciously low (0 or 1)
                            # Even if actual_vertex_count equals vcount, if vcount is 1 and faces require more, we need to update
                            if actual_vertex_count > vcount or (vcount <= 1 and actual_vertex_count > 0):
                                vcount = actual_vertex_count
                                bin_node.trimesh.vertex_count = actual_vertex_count
                                vcount_verified = True
                            # Also update if faces require more vertices than we actually read
                            elif required_vertex_count > 0 and required_vertex_count > actual_vertex_count:
                                # Faces require more vertices - use face-based count (faces are authoritative)
                                vcount = required_vertex_count
                                bin_node.trimesh.vertex_count = required_vertex_count
                                vcount_verified = True
                        finally:
                            self._reader_ext.seek(saved_pos)
                elif bin_node.trimesh.vertices_offset not in (0, 0xFFFFFFFF):
                    # Vertices are in MDL: count actual vertices
                    available_bytes = self._reader.size() - bin_node.trimesh.vertices_offset
                    if available_bytes >= 12:  # At least one vertex (12 bytes for Vector3)
                        saved_pos = self._reader.position()
                        try:
                            self._reader.seek(bin_node.trimesh.vertices_offset)
                            actual_vertex_count = 0
                            max_readable = min(available_bytes // 12, 100000)  # Safety limit
                            # But at least what faces require
                            if required_vertex_count > 0:
                                max_readable = max(max_readable, required_vertex_count)
                            
                            # Read vertices until we can't read any more valid ones
                            for i in range(max_readable):
                                if self._reader.position() + 12 > self._reader.size():
                                    break
                                try:
                                    vertex = self._reader.read_vector3()
                                    # Basic sanity check: reasonable float values, not all zeros
                                    if (
                                        all(-1e6 <= coord <= 1e6 for coord in (vertex.x, vertex.y, vertex.z))
                                        and all(not (coord != coord) for coord in (vertex.x, vertex.y, vertex.z))  # Not NaN
                                    ):
                                        actual_vertex_count = i + 1
                                    else:
                                        # Hit invalid vertex data, but if we've read enough for faces, use that
                                        if required_vertex_count > 0 and actual_vertex_count >= required_vertex_count:
                                            actual_vertex_count = required_vertex_count
                                        break
                                except Exception:
                                    # Can't read more, but if we've read enough for faces, use that
                                    if required_vertex_count > 0 and actual_vertex_count >= required_vertex_count:
                                        actual_vertex_count = required_vertex_count
                                    break
                            
                            # If we found more vertices than the header says, use the actual count
                            # CRITICAL: Always update if actual count is greater OR if vcount is suspiciously low (0 or 1)
                            # Even if actual_vertex_count equals vcount, if vcount is 1 and faces require more, we need to update
                            if actual_vertex_count > vcount or (vcount <= 1 and actual_vertex_count > 0):
                                vcount = actual_vertex_count
                                bin_node.trimesh.vertex_count = actual_vertex_count
                                vcount_verified = True
                            # Also update if faces require more vertices than we actually read
                            elif required_vertex_count > 0 and required_vertex_count > actual_vertex_count:
                                # Faces require more vertices - use face-based count (faces are authoritative)
                                vcount = required_vertex_count
                                bin_node.trimesh.vertex_count = required_vertex_count
                                vcount_verified = True
                        finally:
                            self._reader.seek(saved_pos)
                else:
                    # vertices_offset is invalid - try to find vertices by scanning after faces
                    # This is a fallback for corrupted K1 files where vertices_offset is wrong
                    if required_vertex_count > 0 and bin_node.trimesh.offset_to_faces not in (0, 0xFFFFFFFF):
                        saved_pos = self._reader.position()
                        try:
                            # Try to find vertices after the faces array
                            faces_end = bin_node.trimesh.offset_to_faces + (bin_node.trimesh.faces_count * _Face.SIZE)
                            if faces_end < self._reader.size():
                                # Scan forward from faces_end looking for valid vertex data
                                scan_start = faces_end
                                scan_end = min(scan_start + (required_vertex_count * 12 * 2), self._reader.size())  # Scan up to 2x required bytes
                                actual_vertex_count = 0
                                found_valid_offset = None
                                
                                # Try scanning from faces_end
                                for test_offset in range(scan_start, scan_end, 4):  # Try 4-byte aligned offsets
                                    if test_offset + (required_vertex_count * 12) > self._reader.size():
                                        break
                                    try:
                                        self._reader.seek(test_offset)
                                        test_count = 0
                                        for i in range(min(required_vertex_count, 100)):  # Test first 100 vertices
                                            if self._reader.position() + 12 > self._reader.size():
                                                break
                                            vertex = self._reader.read_vector3()
                                            if (
                                                all(-1e6 <= coord <= 1e6 for coord in (vertex.x, vertex.y, vertex.z))
                                                and all(not (coord != coord) for coord in (vertex.x, vertex.y, vertex.z))
                                            ):
                                                test_count = i + 1
                                            else:
                                                break
                                        
                                        # If we found enough vertices, use this offset
                                        if test_count >= min(required_vertex_count, 10):  # Found at least 10 valid vertices
                                            found_valid_offset = test_offset
                                            actual_vertex_count = test_count
                                            # Try to read all required vertices
                                            self._reader.seek(test_offset)
                                            for i in range(required_vertex_count):
                                                if self._reader.position() + 12 > self._reader.size():
                                                    break
                                                vertex = self._reader.read_vector3()
                                                if (
                                                    all(-1e6 <= coord <= 1e6 for coord in (vertex.x, vertex.y, vertex.z))
                                                    and all(not (coord != coord) for coord in (vertex.x, vertex.y, vertex.z))
                                                ):
                                                    actual_vertex_count = i + 1
                                                else:
                                                    break
                                            break
                                    except Exception:
                                        continue
                                
                                # If we found a valid offset, update vertices_offset
                                if found_valid_offset is not None:
                                    bin_node.trimesh.vertices_offset = found_valid_offset
                                    if actual_vertex_count >= required_vertex_count:
                                        vcount = actual_vertex_count
                                        bin_node.trimesh.vertex_count = actual_vertex_count
                                        vcount_verified = True
                                    elif required_vertex_count > 0:
                                        # Use face-based count even if we didn't read all vertices
                                        vcount = required_vertex_count
                                        bin_node.trimesh.vertex_count = required_vertex_count
                                        vcount_verified = True
                            
                            # If we found more vertices than the header says, use the actual count
                            # CRITICAL: Always update if actual count is greater OR if vcount is suspiciously low (0 or 1)
                            # Even if actual_vertex_count equals vcount, if vcount is 1 and faces require more, we need to update
                            if actual_vertex_count > vcount or (vcount <= 1 and actual_vertex_count > 0):
                                vcount = actual_vertex_count
                                bin_node.trimesh.vertex_count = actual_vertex_count
                                vcount_verified = True
                            # Also update if faces require more vertices than we actually read
                            elif required_vertex_count > 0 and required_vertex_count > actual_vertex_count:
                                # Faces require more vertices - use face-based count (faces are authoritative)
                                vcount = required_vertex_count
                                bin_node.trimesh.vertex_count = required_vertex_count
                                vcount_verified = True
                        finally:
                            self._reader.seek(saved_pos)

            node.mesh.vertex_positions = []
            
            # If vertices were read by read_extra and count matches (and wasn't verified/corrected), use them directly
            if not vcount_verified and bin_node.trimesh.vertices and len(bin_node.trimesh.vertices) == vcount:
                node.mesh.vertex_positions = bin_node.trimesh.vertices.copy()
            # If vcount was verified/corrected, we need to re-read ALL vertices from scratch with the corrected count
            # Don't use read_extra vertices since they were read with the wrong count
            elif vcount_verified:
                # Re-read all vertices from scratch with the verified count
                if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX) and self._reader_ext:
                    # Read all vertices from MDX
                    if bin_node.trimesh.mdx_data_offset not in (0, 0xFFFFFFFF) and bin_node.trimesh.mdx_data_size > 0 and vcount > 0:
                        vertex_offset = bin_node.trimesh.mdx_vertex_offset
                        # Read all vertices up to vcount, preserving index positions for face vertex references
                        # Must maintain 1:1 index mapping - faces reference indices directly, so we can't skip vertices
                        for i in range(vcount):
                            seek_pos = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size + vertex_offset
                            if seek_pos + 12 <= self._reader_ext.size():  # Need 12 bytes for Vector3
                                try:
                                    self._reader_ext.seek(seek_pos)
                                    x, y, z = (
                                        self._reader_ext.read_single(),
                                        self._reader_ext.read_single(),
                                        self._reader_ext.read_single(),
                                    )
                                    # Basic sanity check
                                    if all(-1e6 <= coord <= 1e6 for coord in (x, y, z)) and all(not (coord != coord) for coord in (x, y, z)):
                                        node.mesh.vertex_positions.append(Vector3(x, y, z))
                                    else:
                                        # Invalid vertex data - use null vertex to preserve index position
                                        node.mesh.vertex_positions.append(Vector3.from_null())
                                except Exception:
                                    # Can't read this vertex - use null vertex to preserve index position
                                    node.mesh.vertex_positions.append(Vector3.from_null())
                            else:
                                # Bounds check failed - use null vertex to preserve index position
                                node.mesh.vertex_positions.append(Vector3.from_null())
                        # All vertices should have been read (even if some are null)
                        if len(node.mesh.vertex_positions) != vcount:
                            # This shouldn't happen, but if it does, fall back
                            vcount_verified = False
                elif bin_node.trimesh.vertices_offset not in (0, 0xFFFFFFFF):
                    # Read all vertices from MDL
                    if vcount > 0:
                        self._reader.seek(bin_node.trimesh.vertices_offset)
                        # Read all vertices up to vcount, preserving index positions for face vertex references
                        # Must maintain 1:1 index mapping - faces reference indices directly, so we can't skip vertices
                        # Read as many vertices as possible from file, pad with null vertices if needed
                        for i in range(vcount):
                            if self._reader.position() + 12 <= self._reader.size():
                                try:
                                    vertex = self._reader.read_vector3()
                                    # Basic sanity check
                                    if all(-1e6 <= coord <= 1e6 for coord in (vertex.x, vertex.y, vertex.z)) and all(not (coord != coord) for coord in (vertex.x, vertex.y, vertex.z)):
                                        node.mesh.vertex_positions.append(vertex)
                                    else:
                                        # Invalid vertex data - use null vertex to preserve index position
                                        node.mesh.vertex_positions.append(Vector3.from_null())
                                except Exception:
                                    # Can't read this vertex - use null vertex to preserve index position
                                    node.mesh.vertex_positions.append(Vector3.from_null())
                            else:
                                # Bounds check failed - use null vertex to preserve index position
                                node.mesh.vertex_positions.append(Vector3.from_null())
                        # All vertices should have been read (even if some are null)
                        if len(node.mesh.vertex_positions) != vcount:
                            # This shouldn't happen, but if it does, pad with null vertices
                            while len(node.mesh.vertex_positions) < vcount:
                                node.mesh.vertex_positions.append(Vector3.from_null())
            elif bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX) and self._reader_ext:
                # Read from MDX
                if bin_node.trimesh.mdx_data_offset not in (0, 0xFFFFFFFF) and bin_node.trimesh.mdx_data_size > 0 and vcount > 0:
                    vertex_offset = bin_node.trimesh.mdx_vertex_offset
                    for i in range(vcount):
                        seek_pos = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size + vertex_offset
                        if seek_pos + 12 <= self._reader_ext.size():  # Need 12 bytes for Vector3
                            self._reader_ext.seek(seek_pos)
                            x, y, z = (
                                self._reader_ext.read_single(),
                                self._reader_ext.read_single(),
                                self._reader_ext.read_single(),
                            )
                            node.mesh.vertex_positions.append(Vector3(x, y, z))
                        else:
                            # Bounds check failed, stop reading
                            break
            else:
                # Read from MDL vertex table
                if vcount > 0 and bin_node.trimesh.vertices_offset not in (0, 0xFFFFFFFF):
                    # `read_extra` might have skipped vertices due to a conservative bounds check;
                    # try again here using the advertised vertex_count.
                    vertices_bytes = vcount * 12
                    if bin_node.trimesh.vertices_offset + vertices_bytes <= self._reader.size():
                        self._reader.seek(bin_node.trimesh.vertices_offset)
                        node.mesh.vertex_positions = [self._reader.read_vector3() for _ in range(vcount)]
                    elif bin_node.trimesh.vertices:
                        # Use whatever vertices were read by read_extra, even if incomplete
                        # But try to read the rest if possible
                        node.mesh.vertex_positions = bin_node.trimesh.vertices.copy()
                        remaining = vcount - len(bin_node.trimesh.vertices)
                        if remaining > 0:
                            remaining_bytes = remaining * 12
                            read_pos = bin_node.trimesh.vertices_offset + (len(bin_node.trimesh.vertices) * 12)
                            if read_pos + remaining_bytes <= self._reader.size():
                                self._reader.seek(read_pos)
                                node.mesh.vertex_positions.extend([self._reader.read_vector3() for _ in range(remaining)])
                elif bin_node.trimesh.vertices:
                    # Use vertices read by read_extra
                    node.mesh.vertex_positions = bin_node.trimesh.vertices.copy()

            # Fallback: create null vertices if we couldn't read any, but only if vcount > 0
            if not node.mesh.vertex_positions and vcount > 0:
                # Don't create null vertices if we have some vertices but not all
                # This indicates a real reading problem
                if vcount > 1:
                    # Try one more time to read from MDL if we haven't tried yet
                    if bin_node.trimesh.vertices_offset not in (0, 0xFFFFFFFF):
                        vertices_bytes = vcount * 12
                        if bin_node.trimesh.vertices_offset + vertices_bytes <= self._reader.size():
                            self._reader.seek(bin_node.trimesh.vertices_offset)
                            node.mesh.vertex_positions = [self._reader.read_vector3() for _ in range(vcount)]
                if not node.mesh.vertex_positions:
                    node.mesh.vertex_positions = [Vector3.from_null() for _ in range(vcount)]

            if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL) and self._reader_ext:
                node.mesh.vertex_normals = []
            if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1) and self._reader_ext:
                node.mesh.vertex_uv1 = []
                node.mesh.vertex_uvs = node.mesh.vertex_uv1
            if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE2) and self._reader_ext:
                node.mesh.vertex_uv2 = []

            mdx_offset: int = bin_node.trimesh.mdx_data_offset
            mdx_block_size: int = bin_node.trimesh.mdx_data_size
            for i in range(vcount):
                if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL) and self._reader_ext:
                    if node.mesh.vertex_normals is None:
                        node.mesh.vertex_normals = []
                    normal_pos = mdx_offset + i * mdx_block_size + bin_node.trimesh.mdx_normal_offset
                    if normal_pos + 12 <= self._reader_ext.size():  # Need 12 bytes for Vector3
                        self._reader_ext.seek(normal_pos)
                        x, y, z = (
                            self._reader_ext.read_single(),
                            self._reader_ext.read_single(),
                            self._reader_ext.read_single(),
                        )
                        node.mesh.vertex_normals.append(Vector3(x, y, z))
                    else:
                        # Bounds check failed - use null normal
                        node.mesh.vertex_normals.append(Vector3.from_null())

                if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1 and self._reader_ext:
                    assert node.mesh.vertex_uv1 is not None
                    uv1_pos = mdx_offset + i * mdx_block_size + bin_node.trimesh.mdx_texture1_offset
                    if uv1_pos + 8 <= self._reader_ext.size():  # Need 8 bytes for Vector2
                        self._reader_ext.seek(uv1_pos)
                        u, v = (
                            self._reader_ext.read_single(),
                            self._reader_ext.read_single(),
                        )
                        node.mesh.vertex_uv1.append(Vector2(u, v))
                    else:
                        # Bounds check failed - use null UV
                        node.mesh.vertex_uv1.append(Vector2(0.0, 0.0))

                if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE2 and self._reader_ext:
                    assert node.mesh.vertex_uv2 is not None
                    uv2_pos = mdx_offset + i * mdx_block_size + bin_node.trimesh.mdx_texture2_offset
                    if uv2_pos + 8 <= self._reader_ext.size():  # Need 8 bytes for Vector2
                        self._reader_ext.seek(uv2_pos)
                        u, v = (
                            self._reader_ext.read_single(),
                            self._reader_ext.read_single(),
                        )
                        node.mesh.vertex_uv2.append(Vector2(u, v))
                    else:
                        # Bounds check failed - use null UV
                        node.mesh.vertex_uv2.append(Vector2(0.0, 0.0))

            # If we couldn't load normals (no MDX or no NORMAL flag), keep a sane default.
            if node.mesh.vertex_normals is None:
                node.mesh.vertex_normals = [Vector3.from_null() for _ in range(vcount)]

            for bin_face in bin_node.trimesh.faces:
                face = MDLFace()
                node.mesh.faces.append(face)
                face.v1 = bin_face.vertex1
                face.v2 = bin_face.vertex2
                face.v3 = bin_face.vertex3
                face.a1 = bin_face.adjacent1
                face.a2 = bin_face.adjacent2
                face.a3 = bin_face.adjacent3
                face.normal = bin_face.normal
                face.coefficient = int(bin_face.plane_coefficient)
                # Unpack material into material (low 5 bits) and smoothgroup (high bits)
                # This ensures the internal MDLFace state is canonical (split fields).
                packed = bin_face.material
                face.material = packed & 0x1F
                face.smoothgroup = packed >> 5

            # Preserve inverted_counters and indices arrays for roundtrip compatibility
            if bin_node.trimesh.inverted_counters:
                node.mesh.inverted_counters = bin_node.trimesh.inverted_counters.copy()
            if bin_node.trimesh.indices_counts:
                node.mesh.indices_counts = bin_node.trimesh.indices_counts.copy()
            if bin_node.trimesh.indices_offsets:
                node.mesh.indices_offsets = bin_node.trimesh.indices_offsets.copy()
            # Preserve original indices_offsets_count from binary header even if array is empty
            # This is needed for MDLOps compatibility when the count > 0 but array couldn't be read
            if not hasattr(node.mesh, "indices_offsets_count") or getattr(node.mesh, "indices_offsets_count", None) is None:
                setattr(node.mesh, "indices_offsets_count", bin_node.trimesh.indices_offsets_count)

            # Deterministically derive binary-only face payload from mesh geometry so
            # binary and ASCII parse paths converge (no ASCII syntax extensions).
            if not self._fast_load:
                _mdl_recompute_mesh_face_payload(node.mesh)

        if bin_node.skin:
            node.skin = MDLSkin()
            node.skin.bone_indices = bin_node.skin.bones
            node.skin.bonemap = bin_node.skin.bonemap
            node.skin.tbones = bin_node.skin.tbones
            node.skin.qbones = bin_node.skin.qbones

            if self._reader_ext:
                assert bin_node.trimesh is not None
                for i in range(bin_node.trimesh.vertex_count):
                    vertex_bone = MDLBoneVertex()
                    node.skin.vertex_bones.append(vertex_bone)

                    mdx_offset = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size
                    bones_pos = mdx_offset + bin_node.skin.offset_to_mdx_bones
                    if bones_pos + 16 <= self._reader_ext.size():
                        self._reader_ext.seek(bones_pos)
                        t1 = self._reader_ext.read_single()
                        t2 = self._reader_ext.read_single()
                        t3 = self._reader_ext.read_single()
                        t4 = self._reader_ext.read_single()
                        vertex_bone.vertex_indices = (t1, t2, t3, t4)

                    mdx_offset = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size
                    weights_pos = mdx_offset + bin_node.skin.offset_to_mdx_weights
                    if weights_pos + 16 <= self._reader_ext.size():
                        self._reader_ext.seek(weights_pos)
                        w1 = self._reader_ext.read_single()
                        w2 = self._reader_ext.read_single()
                        w3 = self._reader_ext.read_single()
                        w4 = self._reader_ext.read_single()
                        vertex_bone.vertex_weights = (w1, w2, w3, w4)

        for child_offset in bin_node.children_offsets:
            child_node: MDLNode = self._load_node(child_offset)
            node.children.append(child_node)

        # Skip controllers when fast loading (not needed for rendering)
        if not self._fast_load:
            for i in range(bin_node.header.controller_count):
                offset = bin_node.header.offset_to_controllers + i * _Controller.SIZE
                controller: MDLController = self._load_controller(
                    offset,
                    bin_node.header.offset_to_controller_data,
                )
                node.controllers.append(controller)

        return node

    def _load_anim(
        self,
        offset,
    ) -> MDLAnimation:
        self._reader.seek(offset)

        bin_anim: _AnimationHeader = _AnimationHeader().read(self._reader)

        bin_events: list[_EventStructure] = []
        self._reader.seek(bin_anim.offset_to_events)
        for _ in range(bin_anim.event_count):
            bin_event: _EventStructure = _EventStructure().read(self._reader)
            bin_events.append(bin_event)

        anim = MDLAnimation()

        anim.name = bin_anim.geometry.model_name
        anim.root_model = bin_anim.root
        anim.anim_length = bin_anim.duration
        anim.transition_length = bin_anim.transition

        for bin_event in bin_events:
            event = MDLEvent()
            event.name = bin_event.event_name
            event.activation_time = bin_event.activation_time
            anim.events.append(event)

        anim.root = self._load_node(bin_anim.geometry.root_node_offset)

        return anim

    def _load_controller(
        self,
        offset: int,
        data_offset: int,
    ) -> MDLController:
        self._reader.seek(offset)
        bin_controller: _Controller = _Controller().read(self._reader)

        row_count: int = bin_controller.row_count
        column_count: int = bin_controller.column_count

        # key_offset/data_offset are stored as uint16 float-index offsets relative to the start of the
        # controller-data block (not byte offsets). Convert to bytes when seeking.
        self._reader.seek(data_offset + (bin_controller.key_offset * 4))
        # Read time keys with bounds checking
        time_keys: list[float] = []
        bytes_per_key = 4  # Each float is 4 bytes
        for _ in range(row_count):
            # Check bounds before reading each key
            if self._reader.position() + bytes_per_key > self._reader.size():
                break
            time_keys.append(self._reader.read_single())

        # There are some special cases when reading controller data rows.
        data_pointer: int = data_offset + (bin_controller.data_offset * 4)
        self._reader.seek(data_pointer)

        # Detect bezier interpolation flag (bit 4 = 0x10) in column count
        # vendor/mdlops/MDLOpsM.pm:1704-1710 - Bezier flag detection
        # vendor/mdlops/MDLOpsM.pm:1749-1756 - Bezier data expansion (3 values per column)
        bezier_flag: int = 0x10
        is_bezier: bool = bool(column_count & bezier_flag)

        # Declare data variable once before the if/else block
        data: list[list[float]] = []

        # Orientation data stored in controllers is sometimes compressed into 4 bytes. We need to check for that and
        # uncompress the quaternion if that is the case.
        # vendor/mdlops/MDLOpsM.pm:1714-1719 - Compressed quaternion detection
        # Compressed quaternions use column_count=2, which means 2 floats per row: compressed uint32 + padding float
        # When reading, we read the uint32 directly (not as float), then skip the padding float
        if bin_controller.type_id == MDLControllerType.ORIENTATION and bin_controller.column_count == 2:
            # Detected compressed quaternions - set the model flag
            self._mdl.compress_quaternions = 1
            for _ in range(bin_controller.row_count):
                # Check bounds before reading - need 8 bytes (uint32 + float)
                if self._reader.position() + 8 > self._reader.size():
                    break
                compressed: int = self._reader.read_uint32()
                # Skip padding float that comes after each compressed uint32
                _ = self._reader.read_single()
                decompressed: Vector4 = Vector4.from_compressed(compressed)
                data.append([decompressed.x, decompressed.y, decompressed.z, decompressed.w])
        else:
            # vendor/mdlops/MDLOpsM.pm:1721-1726 - Bezier data reading
            # Bezier controllers store 3 floats per column: (value, in_tangent, out_tangent)
            # Non-bezier controllers store 1 float per column
            if is_bezier:
                base_columns = column_count - bezier_flag
                effective_columns = base_columns * 3
            else:
                effective_columns = column_count

            # Ensure we have at least some columns to read
            if effective_columns <= 0:
                effective_columns = column_count & ~bezier_flag  # Strip bezier flag

            # Read controller data with bounds checking
            bytes_per_row = effective_columns * 4  # Each float is 4 bytes
            for _ in range(row_count):
                # Check bounds before reading each row
                if self._reader.position() + bytes_per_row > self._reader.size():
                    break
                row_data: list[float] = [self._reader.read_single() for _ in range(effective_columns)]
                data.append(row_data)

        controller_type: int = bin_controller.type_id
        # Handle case where we didn't read all rows due to bounds issues
        actual_row_count = min(len(time_keys), len(data), row_count)
        rows: list[MDLControllerRow] = [MDLControllerRow(time_keys[i], data[i]) for i in range(actual_row_count)]
        # vendor/mdlops/MDLOpsM.pm:1709 - Store bezier flag with controller
        controller = MDLController(MDLControllerType(controller_type), rows, is_bezier=is_bezier)
        return controller


class MDLBinaryWriter:
    """Binary MDL/MDX file writer.

    Writes MDL (model) and MDX (model extension) files from MDL data structures.

    References:
    ----------
        vendor/mdlops/MDLOpsM.pm (Binary MDL writing paths)
        vendor/reone/src/libs/graphics/format/mdlmdxwriter.cpp (MDL/MDX writing)
        vendor/kotorblender/format/mdl/writer.py (MDL writing reference)
    """

    def __init__(
        self,
        mdl: MDL,
        target: TARGET_TYPES,
        target_ext: TARGET_TYPES | None,
    ):
        self._mdl: MDL = mdl

        self._target: TARGET_TYPES = target
        self._target_ext: TARGET_TYPES | None = target_ext
        self._writer: BinaryWriterBytearray = BinaryWriter.to_bytearray()
        self._writer_ext: BinaryWriterBytearray = BinaryWriter.to_bytearray()

        self.game: Game = Game.K1

        self._name_offsets: list[int] = []
        self._anim_offsets: list[int] = []
        self._node_offsets: list[int] = []

        self._bin_anim_nodes: dict[str, _Node] = {}
        self._mdl_nodes: list[MDLNode] = []
        self._bin_nodes: list[_Node] = []
        self._bin_anims: list[_Animation] = []
        self._names: list[str] = []
        self._file_header: _ModelHeader = _ModelHeader()

    def write(
        self,
        auto_close: bool = True,
    ):
        self._mdl_nodes[:] = self._mdl.all_nodes()
        self._bin_nodes[:] = [_Node() for _ in self._mdl_nodes]
        self._bin_anims[:] = [_Animation() for _ in self._mdl.anims]
        # Name table must cover *all* nodes referenced by the file: geometry nodes + animation nodes.
        # Some round-trip paths construct animation roots independently, so build this as a de-duped,
        # insertion-ordered list.
        self._names.clear()

        def _add_name(n: str) -> None:
            if n and n not in self._names:
                self._names.append(n)

        for node in self._mdl_nodes:
            _add_name(node.name)
        for anim in self._mdl.anims:
            for node in anim.all_nodes():
                _add_name(node.name)

        self._anim_offsets[:] = [0 for _ in self._bin_anims]
        self._node_offsets[:] = [0 for _ in self._bin_nodes]
        self._file_header = _ModelHeader()

        self._update_all_data()

        self._calc_top_offsets()
        self._calc_inner_offsets()

        self._write_all()

        if auto_close:
            self._writer.close()
            if self._writer_ext is not None:
                self._writer_ext.close()

    def _update_all_data(self):
        for i, bin_node in enumerate(self._bin_nodes):
            self._update_node(bin_node, self._mdl_nodes[i], node_id_override=i)

        for i, bin_anim in enumerate(self._bin_anims):
            self._update_anim(bin_anim, self._mdl.anims[i])

    def _update_node(
        self,
        bin_node: _Node,
        mdl_node: MDLNode,
        *,
        node_id_override: int | None = None,
    ):
        assert bin_node.header is not None
        bin_node.header.type_id = self._node_type(mdl_node)
        bin_node.header.position = mdl_node.position
        bin_node.header.orientation = mdl_node.orientation
        # Clamp children_count to prevent Perl from interpreting it as negative (values >= 2^31)
        # MDLOps reads this as a signed integer, so we must ensure it's < 2^31
        children_count = len(mdl_node.children)
        if children_count > 0x7FFFFFFF:
            children_count = 0x7FFFFFFF
        bin_node.header.children_count = bin_node.header.children_count2 = children_count
        if mdl_node.name not in self._names:
            self._names.append(mdl_node.name)
        bin_node.header.name_id = self._names.index(mdl_node.name)
        # Node IDs are positional within their node array (geometry or animation), not global by name.
        # When writing, always prefer the caller-provided order.
        bin_node.header.node_id = node_id_override if node_id_override is not None else 0

        # Determine the appropriate function pointer values to write
        if self.game == Game.K1:
            if mdl_node.skin:
                fp0 = _TrimeshHeader.K1_SKIN_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_SKIN_FUNCTION_POINTER1
            elif mdl_node.dangly:
                fp0 = _TrimeshHeader.K1_DANGLY_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_DANGLY_FUNCTION_POINTER1
            else:
                fp0 = _TrimeshHeader.K1_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_FUNCTION_POINTER1
        elif mdl_node.skin:
            fp0 = _TrimeshHeader.K2_SKIN_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_SKIN_FUNCTION_POINTER1
        elif mdl_node.dangly:
            fp0 = _TrimeshHeader.K2_DANGLY_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_DANGLY_FUNCTION_POINTER1
        else:
            fp0 = _TrimeshHeader.K2_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_FUNCTION_POINTER1

        if mdl_node.mesh:
            bin_node.trimesh = _TrimeshHeader()
            bin_node.trimesh.function_pointer0 = fp0
            bin_node.trimesh.function_pointer1 = fp1
            bin_node.trimesh.average = mdl_node.mesh.average
            bin_node.trimesh.radius = mdl_node.mesh.radius
            bin_node.trimesh.bounding_box_max = mdl_node.mesh.bb_max
            bin_node.trimesh.bounding_box_min = mdl_node.mesh.bb_min
            bin_node.trimesh.total_area = mdl_node.mesh.area
            bin_node.trimesh.texture1 = mdl_node.mesh.texture_1
            bin_node.trimesh.texture2 = mdl_node.mesh.texture_2
            bin_node.trimesh.diffuse = mdl_node.mesh.diffuse.bgr_vector3()
            bin_node.trimesh.ambient = mdl_node.mesh.ambient.bgr_vector3()
            # render is stored as uint8 in binary (0 or 1), convert from bool to int
            # Ensure we preserve the exact value: False -> 0, True -> 1
            bin_node.trimesh.render = 1 if mdl_node.mesh.render else 0
            bin_node.trimesh.transparency_hint = mdl_node.mesh.transparency_hint
            bin_node.trimesh.uv_jitter = mdl_node.mesh.uv_jitter
            bin_node.trimesh.uv_speed = mdl_node.mesh.uv_jitter_speed
            bin_node.trimesh.uv_direction.x = mdl_node.mesh.uv_direction_x
            bin_node.trimesh.uv_direction.y = mdl_node.mesh.uv_direction_y
            # Flags are stored as uint8 in binary (0 or 1), convert from bool to int
            # Ensure we preserve the exact value: False -> 0, True -> 1
            bin_node.trimesh.has_lightmap = 1 if mdl_node.mesh.has_lightmap else 0
            bin_node.trimesh.rotate_texture = 1 if mdl_node.mesh.rotate_texture else 0
            bin_node.trimesh.background = 1 if mdl_node.mesh.background_geometry else 0
            bin_node.trimesh.has_shadow = 1 if mdl_node.mesh.shadow else 0
            bin_node.trimesh.beaming = 1 if mdl_node.mesh.beaming else 0
            # render is already set above, no need to set it again
            bin_node.trimesh.dirt_enabled = 1 if mdl_node.mesh.dirt_enabled else 0
            bin_node.trimesh.dirt_texture = mdl_node.mesh.dirt_texture
            bin_node.trimesh.dirt_coordinate_space = mdl_node.mesh.dirt_coordinate_space
            bin_node.trimesh.saber_unknowns = bytes(mdl_node.mesh.saber_unknowns)

            bin_node.trimesh.vertex_count = len(mdl_node.mesh.vertex_positions)
            bin_node.trimesh.vertices = mdl_node.mesh.vertex_positions

            # Preserve indices arrays and inverted_counters if they were read from the original binary
            # These are needed for MDLOps compatibility
            if hasattr(mdl_node.mesh, "inverted_counters") and mdl_node.mesh.inverted_counters:
                bin_node.trimesh.inverted_counters = list(mdl_node.mesh.inverted_counters)
                bin_node.trimesh.counters_count = bin_node.trimesh.counters_count2 = len(bin_node.trimesh.inverted_counters)
            else:
                # If not preserved, use empty arrays (MDLOps will regenerate them)
                bin_node.trimesh.inverted_counters = []
                bin_node.trimesh.counters_count = bin_node.trimesh.counters_count2 = 0

            # Preserve indices arrays if available from original binary
            if hasattr(mdl_node.mesh, "indices_counts") and mdl_node.mesh.indices_counts:
                bin_node.trimesh.indices_counts = list(mdl_node.mesh.indices_counts)
            else:
                bin_node.trimesh.indices_counts = []
            if hasattr(mdl_node.mesh, "indices_offsets") and mdl_node.mesh.indices_offsets:
                bin_node.trimesh.indices_offsets = list(mdl_node.mesh.indices_offsets)
            else:
                bin_node.trimesh.indices_offsets = []
            bin_node.trimesh.indices_counts_count = bin_node.trimesh.indices_counts_count2 = len(bin_node.trimesh.indices_counts)
            # Preserve original indices_offsets_count from binary header if available, otherwise use array length
            if hasattr(mdl_node.mesh, "indices_offsets_count") and getattr(mdl_node.mesh, "indices_offsets_count", None) is not None:
                original_count = getattr(mdl_node.mesh, "indices_offsets_count")
                # Use original count if it's > 0, otherwise use array length
                if original_count > 0:
                    bin_node.trimesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count2 = original_count
                    # Ensure array matches count - if count > 0 but array is empty, create array of zeros
                    if not bin_node.trimesh.indices_offsets:
                        bin_node.trimesh.indices_offsets = [0] * original_count
                else:
                    bin_node.trimesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count2 = len(bin_node.trimesh.indices_offsets)
            else:
                bin_node.trimesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count2 = len(bin_node.trimesh.indices_offsets)

            bin_node.trimesh.faces_count = bin_node.trimesh.faces_count2 = len(mdl_node.mesh.faces)
            for face in mdl_node.mesh.faces:
                bin_face = _Face()
                bin_node.trimesh.faces.append(bin_face)
                bin_face.vertex1 = face.v1
                bin_face.vertex2 = face.v2
                bin_face.vertex3 = face.v3
                bin_face.adjacent1 = face.a1
                bin_face.adjacent2 = face.a2
                bin_face.adjacent3 = face.a3
                # Repack surface material (low 5 bits) and smoothgroup (high bits)
                surface = getattr(face, "material", 0) & 0x1F
                smooth = getattr(face, "smoothgroup", 0)
                bin_face.material = surface | (smooth << 5)
                bin_face.plane_coefficient = face.coefficient
                bin_face.normal = face.normal

        # Skin header + extra blocks (bonemap/qbones/tbones) + per-vertex MDX bones/weights.
        if mdl_node.skin:
            bin_node.skin = _SkinmeshHeader()
            skin = mdl_node.skin

            # Bone indices table in header is fixed-size (16 uint16).
            bones = list(getattr(skin, "bone_indices", []))
            bones16: list[int] = [(int(b) if i < len(bones) else -1) for i, b in enumerate(bones[:16] + [-1] * 16)]
            bin_node.skin.bones = tuple(int(b) for b in bones16[:16])

            # Bonemap + bind pose transforms.
            bonemap = list(getattr(skin, "bonemap", []))
            bin_node.skin.bonemap = [int(x) for x in bonemap]
            bin_node.skin.bonemap_count = len(bin_node.skin.bonemap)

            qbones = list(getattr(skin, "qbones", []))
            tbones = list(getattr(skin, "tbones", []))
            bin_node.skin.qbones = list(qbones)
            bin_node.skin.tbones = list(tbones)
            bin_node.skin.qbones_count = bin_node.skin.qbones_count2 = len(bin_node.skin.qbones)
            bin_node.skin.tbones_count = bin_node.skin.tbones_count2 = len(bin_node.skin.tbones)

            # Unknown0 block currently not modeled.
            bin_node.skin.unknown0_count = bin_node.skin.unknown0_count2 = 0
            bin_node.skin.offset_to_unknown0 = 0

            # Offsets to bonemap/qbones/tbones are filled in _calc_skin_offsets().
            bin_node.skin.offset_to_bonemap = 0
            bin_node.skin.offset_to_qbones = 0
            bin_node.skin.offset_to_tbones = 0

            # MDX per-vertex bones/weights offsets are filled in _update_mdx().
            bin_node.skin.offset_to_mdx_bones = 0
            bin_node.skin.offset_to_mdx_weights = 0

        # Emitter header data
        if mdl_node.emitter:
            bin_node.emitter = _EmitterHeader()
            emitter = mdl_node.emitter
            bin_node.emitter.dead_space = emitter.dead_space
            bin_node.emitter.blast_radius = emitter.blast_radius
            bin_node.emitter.blast_length = emitter.blast_length
            bin_node.emitter.branch_count = emitter.branch_count
            bin_node.emitter.smoothing = emitter.control_point_smoothing
            bin_node.emitter.grid = Vector2(float(emitter.x_grid), float(emitter.y_grid))
            bin_node.emitter.update = emitter.update
            bin_node.emitter.render = emitter.render
            bin_node.emitter.blend = emitter.blend
            bin_node.emitter.texture = emitter.texture
            bin_node.emitter.chunk_name = emitter.chunk_name
            bin_node.emitter.twosided_texture = emitter.two_sided_texture
            bin_node.emitter.loop = emitter.loop
            bin_node.emitter.render_order = emitter.render_order
            bin_node.emitter.frame_blending = emitter.frame_blender
            bin_node.emitter.depth_texture = emitter.depth_texture
            bin_node.emitter.unknown0 = 0  # TODO: preserve if available
            bin_node.emitter.flags = emitter.flags

        # Reference header data
        if mdl_node.reference:
            bin_node.reference = _ReferenceHeader()
            reference = mdl_node.reference
            bin_node.reference.model = reference.model
            bin_node.reference.reattachable = 1 if reference.reattachable else 0

        # Controller key/data offsets are stored as uint16 *byte offsets* relative to the start of
        # the controller-data block (header.offset_to_controller_data).
        #
        # Layout in controller-data block:
        #   [time keys (row_count floats)] + [row data (row_count * data_floats_per_row floats)]
        #
        # References:
        #   - vendor/mdlops/MDLOpsM.pm:1649-1778
        #   - vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:664-690
        cur_float_offset = 0
        for mdl_controller in mdl_node.controllers:
            bin_controller = _Controller()
            bin_controller.type_id = mdl_controller.controller_type
            bin_controller.row_count = len(mdl_controller.rows)
            if bin_controller.row_count == 0:
                continue

            first_row = mdl_controller.rows[0]
            data_floats_per_row = len(first_row.data)
            if data_floats_per_row < 0:
                data_floats_per_row = 0

            # Handle compressed quaternions for orientation controllers
            # If compress_quaternions is set and this is an orientation controller with 4 floats per row,
            # set column_count to 2 (compressed quaternions use 2 columns: compressed uint32 + padding)
            if (
                self._mdl.compress_quaternions == 1
                and mdl_controller.controller_type == MDLControllerType.ORIENTATION
                and data_floats_per_row == 4
            ):
                bin_controller.column_count = 2  # Compressed quaternions use 2 columns
            # Encode bezier flag in column_count bit 4 (16) as per mdlops.
            # For bezier controllers, each logical column stores 3 floats per row.
            elif getattr(mdl_controller, "is_bezier", False):
                logical_cols = data_floats_per_row // 3 if data_floats_per_row >= 3 else data_floats_per_row
                bin_controller.column_count = int(logical_cols) | 16
            else:
                bin_controller.column_count = int(data_floats_per_row)

            # Offsets are float-index offsets into the controller-data array.
            bin_controller.key_offset = cur_float_offset
            bin_controller.data_offset = cur_float_offset + bin_controller.row_count

            # Adjust float offset calculation for compressed quaternions
            # Compressed quaternions use 2 floats per row instead of 4
            if (
                self._mdl.compress_quaternions == 1
                and mdl_controller.controller_type == MDLControllerType.ORIENTATION
                and data_floats_per_row == 4
            ):
                # Compressed quaternions: 2 floats per row (compressed uint32 + padding)
                cur_float_offset += bin_controller.row_count + (bin_controller.row_count * 2)
            else:
                cur_float_offset += bin_controller.row_count + (bin_controller.row_count * data_floats_per_row)
            bin_node.w_controllers.append(bin_controller)

        bin_node.w_controller_data = []
        for controller in mdl_node.controllers:
            for row in controller.rows:
                bin_node.w_controller_data.append(row.time)
            for row in controller.rows:
                # Handle compressed quaternions for orientation controllers
                # If compress_quaternions is set and this is an orientation controller with 4 floats per row,
                # compress the quaternion data
                if (
                    self._mdl.compress_quaternions == 1
                    and controller.controller_type == MDLControllerType.ORIENTATION
                    and len(row.data) == 4
                ):
                    # Compress quaternion (x, y, z, w) into a single uint32
                    quat = Vector4(row.data[0], row.data[1], row.data[2], row.data[3])
                    compressed = _compress_quaternion(quat)
                    # Write as uint32 (4 bytes) - column_count will be 2 for compressed quaternions
                    bin_node.w_controller_data.append(float(compressed))
                    bin_node.w_controller_data.append(0.0)  # Second column for compressed quaternions
                else:
                    bin_node.w_controller_data.extend(row.data)

        bin_node.header.controller_count = bin_node.header.controller_count2 = len(mdl_node.controllers)
        bin_node.header.controller_data_length = bin_node.header.controller_data_length2 = len(bin_node.w_controller_data)

    def _update_anim(
        self,
        bin_anim: _Animation,
        mdl_anim: MDLAnimation,
    ):
        if self.game == Game.K1:
            bin_anim.header.geometry.function_pointer0 = _GeometryHeader.K1_ANIM_FUNCTION_POINTER0
            bin_anim.header.geometry.function_pointer1 = _GeometryHeader.K1_ANIM_FUNCTION_POINTER1
        else:
            bin_anim.header.geometry.function_pointer0 = _GeometryHeader.K2_ANIM_FUNCTION_POINTER0
            bin_anim.header.geometry.function_pointer1 = _GeometryHeader.K2_ANIM_FUNCTION_POINTER1

        bin_anim.header.geometry.geometry_type = 5
        bin_anim.header.geometry.model_name = mdl_anim.name
        bin_anim.header.geometry.node_count = 0
        bin_anim.header.duration = mdl_anim.anim_length
        bin_anim.header.transition = mdl_anim.transition_length
        bin_anim.header.root = mdl_anim.root_model
        bin_anim.header.event_count = bin_anim.header.event_count2 = len(mdl_anim.events)

        for mdl_event in mdl_anim.events:
            bin_event = _EventStructure()
            bin_event.event_name = mdl_event.name
            bin_event.activation_time = mdl_event.activation_time
            bin_anim.events.append(bin_event)

        all_nodes: list[MDLNode] = mdl_anim.all_nodes()
        bin_nodes: list[_Node] = []
        for node_id, mdl_node in enumerate(all_nodes):
            bin_node = _Node()
            self._update_node(bin_node, mdl_node, node_id_override=node_id)
            bin_nodes.append(bin_node)
        bin_anim.w_nodes = bin_nodes

    def _update_mdx(
        self,
        bin_node: _Node,
        mdl_node: MDLNode,
    ):
        assert bin_node.trimesh is not None
        assert mdl_node.mesh is not None

        bin_node.trimesh.mdx_data_offset = self._writer_ext.size()

        bin_node.trimesh.mdx_vertex_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_normal_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_texture1_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_texture2_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_data_bitmap = 0

        suboffset = 0
        # Vertices are stored in MDL, not MDX. MDX only contains per-vertex data like normals, UVs, and skin data.
        bin_node.trimesh.mdx_vertex_offset = 0xFFFFFFFF

        if mdl_node.mesh.vertex_normals:
            bin_node.trimesh.mdx_normal_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.NORMAL
            suboffset += 12

        # MDLOps requires texture vertex data in MDX if texture name is set
        # Check both list existence and non-empty to ensure we have valid UV data
        vcount = len(mdl_node.mesh.vertex_positions) if mdl_node.mesh.vertex_positions else 0
        uv1_len = len(mdl_node.mesh.vertex_uv1) if mdl_node.mesh.vertex_uv1 else 0
        uv2_len = len(mdl_node.mesh.vertex_uv2) if mdl_node.mesh.vertex_uv2 else 0
        has_uv1 = mdl_node.mesh.vertex_uv1 is not None and uv1_len == vcount and vcount > 0
        has_uv2 = mdl_node.mesh.vertex_uv2 is not None and uv2_len == vcount and vcount > 0

        # Only set TEXTURE1 flag if texture name is valid (not None, not empty, not "NULL")
        has_texture1 = mdl_node.mesh.texture_1 is not None and mdl_node.mesh.texture_1.strip() != "" and mdl_node.mesh.texture_1.upper() != "NULL"

        if has_uv1:
            bin_node.trimesh.mdx_texture1_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEXTURE1
            if _DEBUG_MDL:
                print(
                    f"DEBUG _update_mdx: Node {mdl_node.name} has_uv1=True texture1={mdl_node.mesh.texture_1} bitmap=0x{bin_node.trimesh.mdx_data_bitmap:08X} TEXTURE1={bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1)} texture1_offset={bin_node.trimesh.mdx_texture1_offset}"
                )
            assert bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1, f"Failed to set TEXTURE1 flag for node {mdl_node.name}"
            suboffset += 8
        elif has_texture1 and vcount > 0:
            # Texture name exists but no valid UV data - generate default UV coordinates
            # This ensures MDLOps can find tverts data when it reads the binary
            if not mdl_node.mesh.vertex_uv1 or len(mdl_node.mesh.vertex_uv1) != vcount:
                mdl_node.mesh.vertex_uv1 = [Vector2(0.0, 0.0) for _ in range(vcount)]
            bin_node.trimesh.mdx_texture1_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEXTURE1
            if _DEBUG_MDL:
                print(
                    f"DEBUG _update_mdx: Node {mdl_node.name} has_uv1=False texture1={mdl_node.mesh.texture_1} vcount={vcount} generated default UVs bitmap=0x{bin_node.trimesh.mdx_data_bitmap:08X} TEXTURE1={bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1)}"
                )
            suboffset += 8

        # Only set TEXTURE2 flag if texture name is valid (not None, not empty, not "NULL")
        has_texture2 = mdl_node.mesh.texture_2 is not None and mdl_node.mesh.texture_2.strip() != "" and mdl_node.mesh.texture_2.upper() != "NULL"

        if has_uv2:
            bin_node.trimesh.mdx_texture2_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEXTURE2
            suboffset += 8
        elif has_texture2 and vcount > 0:
            # Texture name exists but no valid UV data - generate default UV coordinates
            if not mdl_node.mesh.vertex_uv2 or len(mdl_node.mesh.vertex_uv2) != vcount:
                mdl_node.mesh.vertex_uv2 = [Vector2(0.0, 0.0) for _ in range(vcount)]
            bin_node.trimesh.mdx_texture2_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEXTURE2
            suboffset += 8

        # Skin nodes store per-vertex bone indices + weights (4 floats each) in MDX.
        if mdl_node.skin and bin_node.skin is not None:
            bin_node.skin.offset_to_mdx_bones = suboffset
            suboffset += 16
            bin_node.skin.offset_to_mdx_weights = suboffset
            suboffset += 16

        # mdx_data_size is the size of ONE vertex's MDX data block (used for calculating offsets when reading)
        # This includes all per-vertex data (normals, UVs, skin data) but NOT padding
        bin_node.trimesh.mdx_data_size = suboffset

        # Write MDX data based on bitmap flags, not just list existence
        # This ensures we only write data that's actually in the MDX structure
        # Write per-vertex data for all vertices
        for i, position in enumerate(mdl_node.mesh.vertex_positions):
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX:
                self._writer_ext.write_vector3(position)
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL:
                # Only write normals if they're actually in MDX (bitmap flag set)
                norm = mdl_node.mesh.vertex_normals[i] if (mdl_node.mesh.vertex_normals and i < len(mdl_node.mesh.vertex_normals)) else Vector3.from_null()
                self._writer_ext.write_vector3(norm)
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1:
                # Only write UV1 if it's actually in MDX (bitmap flag set)
                uv1 = mdl_node.mesh.vertex_uv1[i] if (mdl_node.mesh.vertex_uv1 and i < len(mdl_node.mesh.vertex_uv1)) else Vector2(0.0, 0.0)
                self._writer_ext.write_vector2(uv1)
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE2:
                # Only write UV2 if it's actually in MDX (bitmap flag set)
                uv2 = mdl_node.mesh.vertex_uv2[i] if (mdl_node.mesh.vertex_uv2 and i < len(mdl_node.mesh.vertex_uv2)) else Vector2(0.0, 0.0)
                self._writer_ext.write_vector2(uv2)

            if mdl_node.skin and bin_node.skin is not None:
                # Bone indices/weights are stored as 4 floats each.
                vb = None
                try:
                    vb = mdl_node.skin.vertex_bones[i]
                except Exception:
                    vb = None
                if vb is None:
                    idxs = (-1.0, -1.0, -1.0, -1.0)
                    wts = (0.0, 0.0, 0.0, 0.0)
                else:
                    idxs = tuple(float(x) for x in vb.vertex_indices)
                    wts = tuple(float(x) for x in vb.vertex_weights)
                for x in idxs:
                    self._writer_ext.write_single(float(x))
                for w in wts:
                    self._writer_ext.write_single(float(w))

        # MDX format includes padding after all vertex data blocks
        # Write padding based on bitmap flags to match MDLOps output
        # Padding is one extra element of each data type (normal, UV1, UV2)
        if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL:
            self._writer_ext.write_vector3(Vector3.from_null())
        if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE1:
            self._writer_ext.write_vector2(Vector2.from_null())
        if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEXTURE2:
            self._writer_ext.write_vector2(Vector2.from_null())

    def _calc_top_offsets(
        self,
    ):
        offset_to_name_offsets = _ModelHeader.SIZE

        offset_to_names = offset_to_name_offsets + 4 * len(self._names)
        name_offset = offset_to_names
        for name in self._names:
            self._name_offsets.append(name_offset)
            name_offset += len(name) + 1

        offset_to_anim_offsets = name_offset
        offset_to_anims = name_offset + (4 * len(self._bin_anims))
        anim_offset = offset_to_anims
        for i, anim in enumerate(self._bin_anims):
            self._anim_offsets[i] = anim_offset
            anim_offset += anim.size()

        offset_to_node_offset = anim_offset
        node_offset = offset_to_node_offset
        for i, bin_node in enumerate(self._bin_nodes):
            self._node_offsets[i] = node_offset
            node_offset += bin_node.calc_size(self.game)

        self._file_header.geometry.root_node_offset = offset_to_node_offset
        self._file_header.offset_to_name_offsets = offset_to_name_offsets
        self._file_header.offset_to_super_root = 0
        self._file_header.offset_to_animations = offset_to_anim_offsets

    def _calc_inner_offsets(
        self,
    ):
        for i, bin_anim in enumerate(self._bin_anims):
            bin_anim.header.offset_to_events = self._anim_offsets[i] + bin_anim.events_offset()
            bin_anim.header.geometry.root_node_offset = self._anim_offsets[i] + bin_anim.nodes_offset()

            node_offsets: list[int] = []
            node_offset: int = self._anim_offsets[i] + bin_anim.nodes_offset()
            for bin_node in bin_anim.w_nodes:
                node_offsets.append(node_offset)
                node_offset += bin_node.calc_size(self.game)

            self._calc_node_offsets_for_context(
                bin_nodes=bin_anim.w_nodes,
                bin_offsets=node_offsets,
                mdl_nodes=self._mdl.anims[i].all_nodes(),
            )

        self._calc_node_offsets_for_context(
            bin_nodes=self._bin_nodes,
            bin_offsets=self._node_offsets,
            mdl_nodes=self._mdl_nodes,
        )

    def _calc_node_offsets_for_context(
        self,
        *,
        bin_nodes: list[_Node],
        bin_offsets: list[int],
        mdl_nodes: list[MDLNode],
    ) -> None:
        """Populate per-node child offsets + header offsets for a single node array (geometry OR animation)."""
        if len(bin_nodes) != len(mdl_nodes):
            raise ValueError(f"bin_nodes and mdl_nodes length mismatch ({len(bin_nodes)} vs {len(mdl_nodes)})")

        idx_by_id = {id(n): i for i, n in enumerate(mdl_nodes)}
        parent_by_idx: dict[int, int] = {}
        for parent_idx, parent in enumerate(mdl_nodes):
            for child in parent.children:
                child_idx = idx_by_id.get(id(child))
                if child_idx is not None:
                    parent_by_idx[child_idx] = parent_idx

        for i in range(len(bin_nodes)):
            bin_node = bin_nodes[i]
            mdl_node = mdl_nodes[i]
            node_offset = bin_offsets[i]

            # Child offsets from the MDL node tree
            bin_node.children_offsets = []
            for child in mdl_node.children:
                child_idx = idx_by_id.get(id(child))
                if child_idx is not None:
                    bin_node.children_offsets.append(bin_offsets[child_idx])

            assert bin_node.header is not None
            bin_node.header.offset_to_children = node_offset + bin_node.children_offsets_offset(self.game)
            bin_node.header.offset_to_controllers = node_offset + bin_node.controllers_offset(self.game)
            bin_node.header.offset_to_controller_data = node_offset + bin_node.controller_data_offset(self.game)
            bin_node.header.offset_to_root = 0
            parent_idx = parent_by_idx.get(i)
            bin_node.header.offset_to_parent = bin_offsets[parent_idx] if parent_idx is not None else 0

            if bin_node.trimesh:
                self._calc_trimesh_offsets(node_offset, bin_node)
            if bin_node.skin:
                self._calc_skin_offsets(node_offset, bin_node)

    def _calc_skin_offsets(
        self,
        node_offset: int,
        bin_node: _Node,
    ) -> None:
        assert bin_node.skin is not None
        # Place skin variable payload blocks immediately after the vertex array.
        after_vertices = node_offset + bin_node.vertices_offset(self.game)
        if bin_node.trimesh:
            after_vertices += bin_node.trimesh.vertices_size()

        cur = after_vertices
        if bin_node.skin.bonemap_count:
            bin_node.skin.offset_to_bonemap = cur
            cur += int(bin_node.skin.bonemap_count) * 4
        else:
            bin_node.skin.offset_to_bonemap = 0

        if bin_node.skin.qbones_count:
            bin_node.skin.offset_to_qbones = cur
            cur += int(bin_node.skin.qbones_count) * 16
        else:
            bin_node.skin.offset_to_qbones = 0

        if bin_node.skin.tbones_count:
            bin_node.skin.offset_to_tbones = cur
            cur += int(bin_node.skin.tbones_count) * 12
        else:
            bin_node.skin.offset_to_tbones = 0

        if bin_node.skin.unknown0_count:
            bin_node.skin.offset_to_unknown0 = cur
            cur += int(bin_node.skin.unknown0_count) * 4
        else:
            bin_node.skin.offset_to_unknown0 = 0

    def _calc_trimesh_offsets(
        self,
        node_offset: int,
        bin_node: _Node,
    ):
        assert bin_node.trimesh is not None
        bin_node.trimesh.offset_to_counters = node_offset + bin_node.inverted_counters_offset(self.game)
        bin_node.trimesh.offset_to_indices_counts = node_offset + bin_node.indices_counts_offset(self.game)
        bin_node.trimesh.offset_to_indices_offset = node_offset + bin_node.indices_offsets_offset(self.game)
        # indices_offsets stores offsets relative to the start of the indices data block
        # If indices_offsets is empty but count > 0, create the correct number of offsets (all 0)
        # This ensures the count matches the array length, preventing MDLOps from reading beyond bounds
        if bin_node.trimesh.indices_offsets_count > 0 and not bin_node.trimesh.indices_offsets:
            # No offsets preserved - create the correct number of offsets (all set to 0)
            # This matches the count that was preserved from the original binary header
            bin_node.trimesh.indices_offsets = [0] * bin_node.trimesh.indices_offsets_count
        # If indices_offsets already has values, preserve them (they're already relative offsets)
        # Ensure count matches array length
        if bin_node.trimesh.indices_offsets:
            bin_node.trimesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count2 = len(bin_node.trimesh.indices_offsets)

        bin_node.trimesh.offset_to_faces = node_offset + bin_node.faces_offset(self.game)
        bin_node.trimesh.vertices_offset = node_offset + bin_node.vertices_offset(self.game)

    def _node_type(
        self,
        node: MDLNode,
    ) -> int:
        type_id = 1
        if node.mesh:
            type_id = type_id | MDLNodeFlags.MESH
        if node.skin:
            type_id = type_id | MDLNodeFlags.SKIN
        if node.dangly:
            type_id = type_id | MDLNodeFlags.DANGLY
        if node.saber:
            type_id = type_id | MDLNodeFlags.SABER
        if node.aabb:
            type_id = type_id | MDLNodeFlags.AABB
        if node.emitter:
            type_id = type_id | MDLNodeFlags.EMITTER
        if node.light:
            type_id = type_id | MDLNodeFlags.LIGHT
        if node.reference:
            type_id = type_id | MDLNodeFlags.REFERENCE
        return type_id

    def _write_all(
        self,
    ):
        # CRITICAL: MDX data must be written in node_id order to match the original binary file structure.
        # The all_nodes() traversal returns nodes in a different order than they appear in the binary,
        # so we need to sort by node_id before writing MDX data.
        # Create a list of (bin_node, mdl_node, original_index) tuples sorted by node_id
        node_pairs = [(self._bin_nodes[i], self._mdl_nodes[i], i, getattr(self._mdl_nodes[i], "node_id", i)) for i in range(len(self._bin_nodes))]
        node_pairs_sorted = sorted(node_pairs, key=lambda x: x[3])  # Sort by node_id

        # Write MDX data in node_id order
        for bin_node, mdl_node, orig_idx, node_id in node_pairs_sorted:
            if bin_node.trimesh:
                if _DEBUG_MDL:
                    print(
                        f"DEBUG _write_all: Calling _update_mdx for node {mdl_node.name} (node_id={node_id}, orig_idx={orig_idx}, bin_node_id={id(bin_node)}, trimesh_id={id(bin_node.trimesh)})"
                    )
                self._update_mdx(bin_node, mdl_node)
                if _DEBUG_MDL and bin_node.trimesh.texture1:
                    print(f"DEBUG _write_all: After _update_mdx, node {mdl_node.name} has tex1_off={bin_node.trimesh.mdx_texture1_offset} (trimesh_id={id(bin_node.trimesh)})")

        self._file_header.geometry.function_pointer0 = _GeometryHeader.K1_FUNCTION_POINTER0
        self._file_header.geometry.function_pointer1 = _GeometryHeader.K1_FUNCTION_POINTER1
        self._file_header.geometry.model_name = self._mdl.name
        self._file_header.geometry.node_count = len(self._mdl_nodes)  # TODO: need to include supermodel in count
        self._file_header.geometry.geometry_type = 2
        self._file_header.offset_to_super_root = self._file_header.geometry.root_node_offset
        self._file_header.mdx_size = self._writer_ext.size()

        # Preserve basic model header fields needed for roundtrip tests.
        # `model_type` corresponds to classification in practice.
        self._file_header.model_type = int(self._mdl.classification)
        # unknown0 corresponds to classification_unk1
        self._file_header.unknown0 = self._mdl.classification_unk1
        self._file_header.fog = 1 if self._mdl.fog else 0
        self._file_header.animation_count = self._file_header.animation_count2 = len(self._mdl.anims)
        self._file_header.bounding_box_min = self._mdl.bmin
        self._file_header.bounding_box_max = self._mdl.bmax
        self._file_header.radius = self._mdl.radius
        self._file_header.anim_scale = float(self._mdl.animation_scale)
        self._file_header.supermodel = self._mdl.supermodel
        # TODO self._file_header.mdx_size
        # TODO self._file_header.mdx_offset
        self._file_header.name_offsets_count = self._file_header.name_offsets_count2 = len(self._names)

        self._file_header.write(self._writer)

        for name_offset in self._name_offsets:
            self._writer.write_uint32(name_offset)

        for name in self._names:
            self._writer.write_string(name + "\0", encoding="ascii")

        for anim_offset in self._anim_offsets:
            self._writer.write_uint32(anim_offset)

        for bin_anim in self._bin_anims:
            bin_anim.write(self._writer, self.game)
        for i, bin_node in enumerate(self._bin_nodes):
            if _DEBUG_MDL and bin_node.trimesh and bin_node.trimesh.texture1:
                print(
                    f"DEBUG _write_all: About to write node {i} (name_id={bin_node.header.name_id if bin_node.header else '?'}) texture1={bin_node.trimesh.texture1} bitmap=0x{bin_node.trimesh.mdx_data_bitmap:08X} texture1_offset={bin_node.trimesh.mdx_texture1_offset}"
                )
            bin_node.write(self._writer, self.game)
            if _DEBUG_MDL and bin_node.trimesh and bin_node.trimesh.texture1:
                print(f"DEBUG _write_all: After writing node {i}, texture1_offset={bin_node.trimesh.mdx_texture1_offset}")

        # Write to MDL
        mdl_writer = BinaryWriter.to_auto(self._target)
        mdl_writer.write_uint32(0)
        mdl_writer.write_uint32(self._writer.size())
        mdl_writer.write_uint32(self._writer_ext.size())
        writer_data = self._writer.data()

        if _DEBUG_MDL:
            # Check writer_data BEFORE writing to file
            import struct

            # Check the first trimesh header at position 23890
            if len(writer_data) >= 23890 + 32:  # 32 bytes for the MDX offsets section
                bitmap_at_23890 = struct.unpack("<I", writer_data[23890:23894])[0]
                tex1_off_at_23890 = struct.unpack("<I", writer_data[23890 + 16 : 23890 + 20])[0]
                print(f"DEBUG _write_all: BEFORE file write - at position 23890: bitmap=0x{bitmap_at_23890:08X} tex1_off={tex1_off_at_23890}")

        mdl_writer.write_bytes(writer_data)

        # Write to MDX
        if self._target_ext is not None:
            BinaryWriter.to_auto(self._target_ext).write_bytes(self._writer_ext.data())
