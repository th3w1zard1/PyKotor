from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pykotor.common.misc import Game
from pykotor.resource.formats.mdl.io.binary.headers.trimesh_header import _TrimeshHeader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter
    from utility.common.geometry import Vector3


class _DanglymeshHeader(_TrimeshHeader):
    """Header data for dangly mesh nodes.

    Extends the trimesh header with additional data for dangly meshes,
    which are meshes that have physics-based vertex animation like cloth or hair.

    A dangly mesh contains constraints and physics parameters that control how
    vertices move in response to forces like gravity and wind.

    Attributes:
        offset_to_constraints (int): Offset to constraint data.
        constraints_count (int): Number of constraints.
        constraints_count2 (int): Duplicate of constraints_count.
        displacement (float): Maximum vertex displacement.
        tightness (float): Spring tightness/stiffness.
        period (float): Animation period/frequency.
        unknown0 (int): Unknown value.
        constraints (list[tuple[float, float, float, float]]): Constraint data.
        verts (list[Vector3]): Vertex positions.
        verts_original (list[Vector3]): Original vertex positions.
    """

    K1_SIZE: ClassVar[Literal[360]] = 360
    """Size of the header in bytes for KotOR 1."""

    K2_SIZE: ClassVar[Literal[368]] = 368
    """Size of the header in bytes for KotOR 2."""

    def __init__(self):
        super().__init__()
        self.offset_to_constraints: int = 0
        self.constraints_count: int = 0
        self.constraints_count2: int = 0
        self.displacement: float = 0.0
        self.tightness: float = 0.0
        self.period: float = 0.0
        self.unknown0: int = 0  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.

        # Runtime data
        self.constraints: list[tuple[float, float, float, float]] = []
        self.verts: list[Vector3] = []
        self.verts_original: list[Vector3] = []

    def read(self, reader: BinaryReader) -> _DanglymeshHeader:
        """Read danglymesh header data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated danglymesh header instance.
        """
        super().read(reader)
        self.offset_to_constraints = reader.read_uint32()
        self.constraints_count = reader.read_uint32()
        self.constraints_count2 = reader.read_uint32()
        self.displacement = reader.read_single()
        self.tightness = reader.read_single()
        self.period = reader.read_single()
        self.unknown0 = reader.read_uint32()  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        return self

    def read_extra(self, reader: BinaryReader):
        """Read additional mesh data referenced by offsets.

        Args:
            reader: Binary reader to read data from.
        """
        super().read_extra(reader)

        # Read constraints - each constraint is 4 floats
        reader.seek(self.offset_to_constraints)
        self.constraints = [
            (
                reader.read_single(),  # type
                reader.read_single(),  # target
                reader.read_single(),  # target_node
                reader.read_single(),  # unknown  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
            )
            for _ in range(self.constraints_count)
        ]

        # Store original vertex positions for physics simulation
        self.verts = self.vertices.copy()
        self.verts_original = self.vertices.copy()

    def write(self, writer: BinaryWriter, game: Game):
        """Write danglymesh header data to a binary stream.

        Args:
            writer: Binary writer to write data to.
            game: Game version (K1/K2) to determine format specifics.
        """
        super().write(writer, game)
        writer.write_uint32(self.offset_to_constraints)
        writer.write_uint32(self.constraints_count)
        writer.write_uint32(self.constraints_count2)
        writer.write_single(self.displacement)
        writer.write_single(self.tightness)
        writer.write_single(self.period)
        writer.write_uint32(self.unknown0)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.

    def header_size(self, game: Game) -> int:
        """Get size of header for given game version.

        Args:
            game: Game version (K1/K2) to determine format specifics.

        Returns:
            int: Header size in bytes.
        """
        return _DanglymeshHeader.K1_SIZE if game == Game.K1 else _DanglymeshHeader.K2_SIZE
