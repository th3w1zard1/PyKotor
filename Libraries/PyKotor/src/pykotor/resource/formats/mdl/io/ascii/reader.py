"""ASCII MDLModel file reader implementation."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.io.base_reader import MDLReader
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.model import MDL


class MDLASCIIReader(MDLReader):
    """Reader for ASCII MDL files."""

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader):
        """Initialize the reader.

        Args:
            mdl_reader: The reader to use for reading the MDL file
            mdx_reader: The reader to use for reading the MDX file
        """
        super().__init__(mdl_reader, mdx_reader)
        self._isgeometry: bool = False  # true if we are in model geometry
        self._isanimation: bool = False  # true if we are in animations
        self._innode: bool = False  # true if currently processing a node
        self._nodenum: int = 0
        self._animnum: int = 0
        self._task: str = ""  # current parsing task (verts, faces, etc.)
        self._count: int = 0  # counter for current task
        self._current_line: str = ""

    def read(self) -> MDL:
        """Read the ASCII MDL file and return the model.

        Returns:
            MDL: The loaded model

        Raises:
            MDLReadError: If there is an error reading the file
        """
        try:
            # Set default values as per MDLModelops
            self._mdl.bounding_min = Vector3(-5, -5, -1)
            self._mdl.bounding_max = Vector3(5, 5, 10)
            self._mdl.radius = 7.0
            self._mdl.animation_scale = 0.971

            # Process file line by line
            while True:
                line = self._mdl_reader.read_line()
                if not line:
                    break

                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Handle model geometry section
                if line.lower().startswith("beginmodelgeom"):
                    self._isgeometry = True
                    self._nodenum = 0
                elif line.lower().startswith("endmodelgeom"):
                    self._isgeometry = False
                    self._nodenum = 0

                # Handle animation section
                elif line.lower().startswith("newanim"):
                    self._isanimation = True
                    parts = line.split()
                    if len(parts) < 2:
                        raise MDLReadError("Invalid newanim line, missing animation name")
                    self._mdl.anims[self._animnum].name = parts[1]
                    self._mdl.anims[self._animnum].nodelist = []
                    self._mdl.anims[self._animnum].eventtimes = []
                    self._mdl.anims[self._animnum].eventnames = []
                elif line.lower().startswith("doneanim"):
                    self._isanimation = False
                    self._animnum += 1

                # Handle node section
                elif line.lower().startswith("node") and not self._innode:
                    self._innode = True
                    parts = line.split()
                    if len(parts) < 3:
                        raise MDLReadError("Invalid node line, expected 'node type name'")
                    node_type = parts[1].lower()
                    node_name = parts[2]

                    # Create node based on type
                    from pykotor.resource.formats.mdl.io.ascii.nodes.node_factory import MDLASCIINodeReaderFactory
                    factory = MDLASCIINodeReaderFactory(self._mdl_reader, self._mdx_reader, self._names, self._node_by_number)
                    reader = factory.create_reader(node_type)
                    node = reader.read_node()

                    if self._isgeometry:
                        self._mdl.nodes.append(node)
                    elif self._isanimation:
                        self._mdl.anims[self._animnum].nodes.append(node)

                elif line.lower().startswith("endnode"):
                    self._innode = False
                    self._task = ""
                    if self._isgeometry:
                        self._nodenum += 1

            return self._mdl

        except Exception as e:
            raise MDLReadError(f"Error reading ASCII MDL: {str(e)}")

    def _load_names(self) -> None:
        """Load the names list from the file.

        Raises:
            MDLReadError: If there is an error reading names
        """
        try:
            line = self._read_line()
            if not line.startswith("names"):
                return

            parts = line.split()
            if len(parts) < 2:
                raise MDLReadError("Invalid names line, missing count")

            count = int(parts[1])
            if count < 0:
                raise MDLReadError(f"Invalid names count: {count}")

            self._expect_token("{")

            for _ in range(count):
                name = self._read_line().strip('"')
                self._names.append(name)

            self._expect_token("}")

        except Exception as e:
            raise MDLReadError(f"Error reading names: {str(e)}")

    def _peek_nodes(self) -> None:
        """Pre-scan nodes to build node lookup table.

        ASCII format doesn't need pre-scanning since node numbers
        are explicitly defined in the node declarations.
        """
        pass

    def _load_nodes(self) -> None:
        """Load all nodes from the file.

        Raises:
            MDLReadError: If there is an error loading nodes
        """
        try:
            line = self._read_line()
            if not line.startswith("nodes"):
                return

            parts = line.split()
            if len(parts) < 2:
                raise MDLReadError("Invalid nodes line, missing count")

            count = int(parts[1])
            if count < 0:
                raise MDLReadError(f"Invalid nodes count: {count}")

            self._expect_token("{")

            # Node loading will be implemented by specific node readers
            # based on the node type declarations in the ASCII format

            self._expect_token("}")

        except Exception as e:
            raise MDLReadError(f"Error loading nodes: {str(e)}")

    def _load_animations(self) -> None:
        """Load all animations from the file.

        Raises:
            MDLReadError: If there is an error loading animations
        """
        try:
            line = self._read_line()
            if not line.startswith("animations"):
                return

            parts = line.split()
            if len(parts) < 2:
                raise MDLReadError("Invalid animations line, missing count")

            count = int(parts[1])
            if count < 0:
                raise MDLReadError(f"Invalid animations count: {count}")

            self._expect_token("{")

            # Animation loading will be implemented separately
            # following the ASCII format specifications

            self._expect_token("}")

        except Exception as e:
            raise MDLReadError(f"Error loading animations: {str(e)}")

    def _read_line(self) -> str:
        """Read next non-empty, non-comment line.

        Returns:
            str: The next line of content

        Raises:
            MDLReadError: If there is an error reading the line
        """
        try:
            while True:
                line = self._mdl_reader.read_line()
                if not line:
                    raise MDLReadError("Unexpected end of file")

                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                self._current_line = line
                return line

        except Exception as e:
            raise MDLReadError(f"Error reading line: {str(e)}")

    def _expect_token(self, expected: str) -> None:
        """Expect a specific token on the current line.

        Args:
            expected: The expected token

        Raises:
            MDLReadError: If token doesn't match
        """
        if not self._current_line.startswith(expected):
            raise MDLReadError(f"Expected '{expected}', got '{self._current_line}'")

    def _read_string_property(self, name: str) -> str:
        """Read a string property.

        Args:
            name: Property name

        Returns:
            str: Property value

        Raises:
            MDLReadError: If property is invalid
        """
        try:
            line = self._read_line()
            if not line.startswith(name):
                raise MDLReadError(f"Expected '{name}' property")

            parts = line.split('"')
            if len(parts) < 2:
                raise MDLReadError(f"Invalid string property '{name}', missing quotes")

            return parts[1]

        except Exception as e:
            raise MDLReadError(f"Error reading string property '{name}': {str(e)}")

    def _read_single_property(self, name: str) -> float:
        """Read a float property.

        Args:
            name: Property name

        Returns:
            float: Property value

        Raises:
            MDLReadError: If property is invalid
        """
        try:
            line = self._read_line()
            if not line.startswith(name):
                raise MDLReadError(f"Expected '{name}' property")

            parts = line.split()
            if len(parts) < 2:
                raise MDLReadError(f"Invalid float property '{name}', missing value")

            return float(parts[1])

        except Exception as e:
            raise MDLReadError(f"Error reading float property '{name}': {str(e)}")

    def _read_vector3_property(self, name: str) -> tuple[float, float, float]:
        """Read a vector3 property.

        Args:
            name: Property name

        Returns:
            tuple: (x, y, z) values

        Raises:
            MDLReadError: If property is invalid
        """
        try:
            line = self._read_line()
            if not line.startswith(name):
                raise MDLReadError(f"Expected '{name}' property")

            parts = line.split()[1:]
            if len(parts) < 3:
                raise MDLReadError(f"Invalid vector3 property '{name}', expected 3 values")

            return float(parts[0]), float(parts[1]), float(parts[2])

        except Exception as e:
            raise MDLReadError(f"Error reading vector3 property '{name}': {str(e)}")